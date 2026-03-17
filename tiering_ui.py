"""
BK blog analysis – Tiering UI (setup wizard)

Run with: streamlit run tiering_ui.py

Wizard: (1) Profitability, (2) Break-even (year as buttons, utilization as slider).
Results: all assumptions in sidebar; tier distribution, count by config,
total/avg kWh per tier, avg utilization per tier.
"""
BK blog analysis – Tiering UI (setup wizard)

Run with: streamlit run tiering_ui.py

Wizard: (1) Profitability, (2) Break-even (year as buttons, utilization as slider).
Results: all assumptions in sidebar; tier distribution, count by config,
total/avg kWh per tier, avg utilization per tier.
"""
import os
import pandas as pd
import streamlit as st
import altair as alt

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
EXCEL_PATH = os.path.join(SCRIPT_DIR, "BK analyssis.xlsx")

CONFIG_COL = "Configuration"
ID_COL = "Original ID"
NAME_COL = "Location Name"
EST_POTENTIAL_COL = "Estimated Potential"
YEAR_COLS = {
    2026: "Util 2027",
    2027: "Util 2027",
    2030: "Util 2030",
    2035: "Util 2035",
}
YEAR_OPTIONS = [2026, 2027, 2030, 2035]
CONFIG_ORDER = ["2x50", "2x150", "2x300", "4x300", "6x300"]

# Zoniq brand colors for charts
NORTHERN_LIGHTS = "#00EA88"  # primary data
ARCTIC_COLD = "#49FFF4"  # secondary data
CARBON = "#2D3330"  # backgrounds
OFF_WHITE = "#F8F8F8"  # text, borders


@st.cache_data
def load_data():
    return pd.read_excel(EXCEL_PATH, engine="openpyxl")


def init_session_state():
    if "wizard_step" not in st.session_state:
        st.session_state.wizard_step = 0
    if "profit_year" not in st.session_state:
        st.session_state.profit_year = 2027
    if "profit_util_pct" not in st.session_state:
        st.session_state.profit_util_pct = 15.0
    if "break_even_year" not in st.session_state:
        st.session_state.break_even_year = 2027
    if "break_even_util_pct" not in st.session_state:
        st.session_state.break_even_util_pct = 10.0


def assign_tiers_and_recommended_config(
    df, min_config, profit_year, profit_util_pct, break_even_year, break_even_util_pct
):
    col_p = YEAR_COLS[profit_year]
    col_b = YEAR_COLS[break_even_year]
    util_p = profit_util_pct / 100.0
    util_b = break_even_util_pct / 100.0

    configs_in_data = [c for c in CONFIG_ORDER if c in df[CONFIG_COL].values]
    if not configs_in_data:
        configs_in_data = sorted(df[CONFIG_COL].dropna().unique().tolist())

    df_min = df[df[CONFIG_COL] == min_config].drop_duplicates(subset=[ID_COL], keep="first")
    all_ids = set(df[ID_COL].unique())
    loc_to_tier = {}
    for _, row in df_min.iterrows():
        loc_id = row[ID_COL]
        u_p = row.get(col_p)
        u_b = row.get(col_b)
        if pd.notna(u_p) and u_p >= util_p:
            loc_to_tier[loc_id] = "Tier A"
        elif pd.notna(u_b) and u_b >= util_b:
            loc_to_tier[loc_id] = "Tier B"
        else:
            loc_to_tier[loc_id] = "Tier C"
    for loc_id in all_ids - set(df_min[ID_COL]):
        loc_to_tier[loc_id] = "Tier C"

    loc_to_rec_config = {}
    for loc_id in all_ids:
        tier = loc_to_tier[loc_id]
        rows_loc = df[df[ID_COL] == loc_id]
        if tier == "Tier A":
            meets = rows_loc[col_p] >= util_p
        elif tier == "Tier B":
            meets = rows_loc[col_b] >= util_b
        else:
            loc_to_rec_config[loc_id] = min_config if min_config in rows_loc[CONFIG_COL].values else "—"
            continue
        rows_ok = rows_loc[meets]
        if rows_ok.empty:
            loc_to_rec_config[loc_id] = min_config
            continue
        configs_ok = set(rows_ok[CONFIG_COL].unique())
        best = min_config
        for c in configs_in_data:
            if c in configs_ok:
                best = c
        loc_to_rec_config[loc_id] = best

    result = []
    for loc_id in sorted(all_ids):
        result.append({
            ID_COL: loc_id,
            "tier": loc_to_tier[loc_id],
            "recommended_config": loc_to_rec_config.get(loc_id, min_config),
        })
    return pd.DataFrame(result)


def main():
    st.set_page_config(page_title="BK blog analysis – Tiering", layout="wide")
    init_session_state()

    df = load_data()
    configs = sorted(df[CONFIG_COL].dropna().unique().tolist())
    default_min_config = "2x150" if "2x150" in configs else configs[0]
    has_est_potential = EST_POTENTIAL_COL in df.columns
    util_col_agg = "Util 2030"  # for average util by tier

    # ----- Step 0: Profitability (narrow centered layout) -----
    if st.session_state.wizard_step == 0:
        _left, center, _right = st.columns([1, 2, 1])
        with center:
            st.title("Setup – New opportunities")
            st.subheader("Step 1 of 2: Profitability")
            st.markdown("**When do you expect to be profitable for your new opportunities?**")
            year_a = st.radio("Year", YEAR_OPTIONS, index=YEAR_OPTIONS.index(st.session_state.profit_year), key="radio_profit_year", horizontal=True)
            st.markdown("**What utilization rate do you need to achieve to be profitable?**")
            util_a = st.slider("Utilization %", 1, 30, int(st.session_state.profit_util_pct), 1, key="slider_profit_util")
            if st.button("Next"):
                st.session_state.profit_year = year_a
                st.session_state.profit_util_pct = float(util_a)
                st.session_state.wizard_step = 1
                st.rerun()
        return

    # ----- Step 1: Break-even (narrow centered layout, utilization only) -----
    if st.session_state.wizard_step == 1:
        _left, center, _right = st.columns([1, 2, 1])
        with center:
            st.title("Setup – New opportunities")
            st.subheader("Step 2 of 2: Break-even")
            st.markdown("**What utilization rate do you need to achieve to be break-even?**")
            util_b = st.slider("Utilization %", 1, 30, int(st.session_state.break_even_util_pct), 1, key="slider_break_util")
            col1, col2, _ = st.columns([1, 1, 4])
            with col1:
                if st.button("Next"):
                    st.session_state.break_even_util_pct = float(util_b)
                    st.session_state.wizard_step = 2
                    st.rerun()
            with col2:
                if st.button("Back"):
                    st.session_state.wizard_step = 0
                    st.rerun()
        return

    # ----- Step 2: Results – sidebar exposes all assumptions -----
    st.title("Opportunity profitability assessment")

    with st.sidebar:
        st.header("Assumptions")
        min_config = st.selectbox(
            "Minimum configuration (tiers assessed on this config)",
            options=configs,
            index=configs.index(default_min_config) if default_min_config in configs else 0,
            key="side_min_config",
        )
        st.subheader("Profitability - Tier A")
        profit_year = st.radio("Year (profitability)", YEAR_OPTIONS, index=YEAR_OPTIONS.index(st.session_state.profit_year), key="side_profit_year", horizontal=True)
        profit_util_pct = st.slider("Utilization % (profitability)", 1, 30, int(st.session_state.profit_util_pct), 1, key="side_profit_util")
        st.subheader("Break-even - Tier B")
        break_even_util_pct = st.slider("Utilization % (break-even)", 1, 30, int(st.session_state.break_even_util_pct), 1, key="side_break_util")
        # Persist for next run
        st.session_state.profit_year = profit_year
        st.session_state.profit_util_pct = float(profit_util_pct)
        st.session_state.break_even_util_pct = float(break_even_util_pct)

    # Break-even year is aligned to profitability year (no separate control)
    break_even_year = profit_year

    tier_df = assign_tiers_and_recommended_config(
        df, min_config, profit_year, profit_util_pct, break_even_year, break_even_util_pct
    )
    tier_counts_series = tier_df["tier"].value_counts().reindex(["Tier A", "Tier B", "Tier C"], fill_value=0)
    total = tier_counts_series.sum()
    tier_pct_series = (tier_counts_series / total * 100).round(1)

    # Enrich with Estimated Potential and Util from the row matching recommended_config
    if has_est_potential and util_col_agg in df.columns:
        rec_rows = df.merge(tier_df[[ID_COL, "recommended_config"]], on=ID_COL, how="right")
        rec_rows = rec_rows[rec_rows[CONFIG_COL] == rec_rows["recommended_config"]].drop_duplicates(subset=[ID_COL], keep="first")
        tier_df = tier_df.merge(
            rec_rows[[ID_COL, EST_POTENTIAL_COL, util_col_agg]],
            on=ID_COL,
            how="left",
        )
    else:
        tier_df[EST_POTENTIAL_COL] = None
        tier_df[util_col_agg] = None

    st.markdown(
        f"""
- **Tier A (profitability):** Reaches **{profit_util_pct}%** utilization by **{profit_year}** on **{min_config}**.
- **Tier B (break-even):** At least **{break_even_util_pct}%** utilization by **{break_even_year}** on **{min_config}**.
- **Tier C:** All other locations.
"""
    )

    chart_height = 170

    # Row 1: Profitability tiers | Opportunity size
    c1, c2 = st.columns(2)
    with c1:
        st.subheader("Profitability tiers")
        summary = pd.DataFrame({
            "tier": ["Tier A", "Tier B", "Tier C"],
            "count": [int(tier_counts_series["Tier A"]), int(tier_counts_series["Tier B"]), int(tier_counts_series["Tier C"])],
        })
        base1 = alt.Chart(summary).mark_bar(color=NORTHERN_LIGHTS).encode(
            y=alt.Y("tier", sort=["Tier A", "Tier B", "Tier C"], title=None),
            x=alt.X("count", title="Number of locations"),
        ).properties(height=chart_height, background=CARBON)
        labels1 = alt.Chart(summary).mark_text(
            color=OFF_WHITE,
            align="left",
            dx=4,
        ).encode(
            y=alt.Y("tier", sort=["Tier A", "Tier B", "Tier C"]),
            x="count",
            text="count",
        )
        ch1 = (base1 + labels1).configure_axis(
            labelColor=OFF_WHITE,
            titleColor=OFF_WHITE,
        ).configure_view(
            stroke=OFF_WHITE,
        )
        st.altair_chart(ch1, use_container_width=True)
    with c2:
        st.subheader("Opportunity size")
        if has_est_potential and EST_POTENTIAL_COL in tier_df.columns:
            total_kwh_df = tier_df.groupby("tier")[EST_POTENTIAL_COL].sum().reindex(["Tier A", "Tier B", "Tier C"], fill_value=0).reset_index()
            total_kwh_df.columns = ["tier", "total_kwh"]
            base2 = alt.Chart(total_kwh_df).mark_bar(color=ARCTIC_COLD).encode(
                y=alt.Y("tier", sort=["Tier A", "Tier B", "Tier C"], title=None),
                x=alt.X("total_kwh", title="Total kWh/day"),
            ).properties(height=chart_height, background=CARBON)
            labels2 = alt.Chart(total_kwh_df).mark_text(
                color=OFF_WHITE,
                align="left",
                dx=4,
            ).encode(
                y=alt.Y("tier", sort=["Tier A", "Tier B", "Tier C"]),
                x="total_kwh",
                text="total_kwh",
            )
            ch2 = (base2 + labels2).configure_axis(
                labelColor=OFF_WHITE,
                titleColor=OFF_WHITE,
            ).configure_view(
                stroke=OFF_WHITE,
            )
            st.altair_chart(ch2, use_container_width=True)
        else:
            st.caption("No Estimated Potential column in data.")

    # Row 2: Performance averages
    st.markdown("**Performance averages**")
    c3, c4 = st.columns(2)
    with c3:
        st.caption("Average utilization rate by tier")
        if util_col_agg in tier_df.columns and tier_df[util_col_agg].notna().any():
            avg_util_df = (tier_df.groupby("tier")[util_col_agg].mean().reindex(["Tier A", "Tier B", "Tier C"], fill_value=0) * 100).reset_index()
            avg_util_df.columns = ["tier", "avg_util_pct"]
            base3 = alt.Chart(avg_util_df).mark_bar(color=NORTHERN_LIGHTS).encode(
                y=alt.Y("tier", sort=["Tier A", "Tier B", "Tier C"], title=None),
                x=alt.X("avg_util_pct", title="Average utilization (%)"),
            ).properties(height=chart_height, background=CARBON)
            labels3 = alt.Chart(avg_util_df).mark_text(
                color=OFF_WHITE,
                align="left",
                dx=4,
            ).encode(
                y=alt.Y("tier", sort=["Tier A", "Tier B", "Tier C"]),
                x="avg_util_pct",
                text=alt.Text("avg_util_pct:Q", format=".1f"),
            )
            ch3 = (base3 + labels3).configure_axis(
                labelColor=OFF_WHITE,
                titleColor=OFF_WHITE,
            ).configure_view(
                stroke=OFF_WHITE,
            )
            st.altair_chart(ch3, use_container_width=True)
        else:
            st.caption("No utilization data.")
    with c4:
        st.caption("Average estimated kWh/day by tier")
        if has_est_potential and EST_POTENTIAL_COL in tier_df.columns:
            avg_kwh_df = tier_df.groupby("tier")[EST_POTENTIAL_COL].mean().reindex(["Tier A", "Tier B", "Tier C"], fill_value=0).reset_index()
            avg_kwh_df.columns = ["tier", "avg_kwh"]
            base4 = alt.Chart(avg_kwh_df).mark_bar(color=ARCTIC_COLD).encode(
                y=alt.Y("tier", sort=["Tier A", "Tier B", "Tier C"], title=None),
                x=alt.X("avg_kwh", title="Average kWh/day"),
            ).properties(height=chart_height, background=CARBON)
            labels4 = alt.Chart(avg_kwh_df).mark_text(
                color=OFF_WHITE,
                align="left",
                dx=4,
            ).encode(
                y=alt.Y("tier", sort=["Tier A", "Tier B", "Tier C"]),
                x="avg_kwh",
                text=alt.Text("avg_kwh:Q", format=".0f"),
            )
            ch4 = (base4 + labels4).configure_axis(
                labelColor=OFF_WHITE,
                titleColor=OFF_WHITE,
            ).configure_view(
                stroke=OFF_WHITE,
            )
            st.altair_chart(ch4, use_container_width=True)
        else:
            st.caption("No Estimated Potential column in data.")

    # Table alongside charts (kept close for a tighter layout)
    st.subheader("Configurations rightsizing")
    by_tier_config = tier_df.groupby(["tier", "recommended_config"]).size().unstack(fill_value=0)
    by_tier_config = by_tier_config.reindex(["Tier A", "Tier B", "Tier C"], fill_value=0).reset_index()
    st.dataframe(by_tier_config, width="stretch", hide_index=True)


if __name__ == "__main__":
    main()
