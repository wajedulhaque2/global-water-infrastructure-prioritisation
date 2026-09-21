from __future__ import annotations

import pandas as pd
import plotly.express as px
import streamlit as st

from chart_utils import BLUE, GREEN, ORANGE, PILLAR_COLORS, TEAL, style_figure
from model import PILLARS, freshness_status


LABELS = {
    "WATER_ACCESS": "Water access",
    "FRESHWATER_PC": "Renewable freshwater",
    "U5_MORTALITY": "Under-5 mortality",
    "EDUCATION": "Primary completion",
    "GDP_PC_PPP": "GDP per capita PPP",
    "ELECTRICITY": "Electricity access",
    "RURAL_POP": "Rural population",
    "POP_GROWTH": "Population growth",
    "POP_TOTAL": "Total population",
}


def render(scored, scored_latest, history, indicators, comparison, context: dict[str, object]) -> None:
    selected = scored.loc[scored["Country"].eq(context["country"])].iloc[0]
    definitions = indicators.loc[
        indicators["Active"].eq("Yes"),
        ["Indicator ID", "Indicator", "Pillar", "Direction", "Within-Pillar Weight"],
    ].copy()
    observations = scored_latest.loc[
        scored_latest["ISO3"].eq(selected["ISO3"]),
        ["Indicator ID", "ISO3", "Value", "Year", "DataAge", "Need Score"],
    ].copy()
    country_latest = definitions.merge(observations, on="Indicator ID", how="left")
    country_latest["Status"] = country_latest.apply(
        freshness_status,
        axis=1,
        stale_years=context["stale_years"],
        analysis_end_year=context["analysis_end_year"],
    )
    country_latest["Indicator label"] = country_latest["Indicator ID"].map(LABELS)

    st.title("Country priority profile")
    st.caption("Indicator-level evidence, data quality, and scenario sensitivity")
    st.markdown(
        f'<div class="scope-note"><b>{selected["Country"]}</b> · {selected["Region"]} · {selected["IncomeLevel"]}</div>',
        unsafe_allow_html=True,
    )

    cols = st.columns(4)
    cols[0].metric("Global rank", f"{int(selected['Rank']):,}" if pd.notna(selected["Rank"]) else "n.a.")
    cols[1].metric("Priority score", f"{selected['Priority Score']:.1f}" if pd.notna(selected["Priority Score"]) else "n.a.")
    cols[2].metric("Data completeness", f"{selected['Completeness']:.0%}")
    cols[3].metric("Model status", selected["Eligibility"])

    left, right = st.columns(2)
    with left:
        pillars = selected[PILLARS].rename_axis("Pillar").reset_index(name="Score")
        fig = px.bar(pillars, x="Score", y="Pillar", orientation="h", color="Pillar", color_discrete_map=PILLAR_COLORS)
        fig.update_layout(title="Pillar scores", showlegend=False, xaxis_range=[0, 100])
        st.plotly_chart(style_figure(fig, 350), width="stretch", config={"displayModeBar": False})
    with right:
        scenario_country = comparison.loc[comparison["ISO3"].eq(selected["ISO3"])].copy()
        scenario_country["Scenario"] = pd.Categorical(
            scenario_country["Scenario"],
            ["Base Case", "Water-Stress Focus", "Social-Impact Focus", "Custom"],
            ordered=True,
        )
        scenario_country = scenario_country.sort_values("Scenario")
        fig = px.bar(scenario_country, x="Priority Score", y="Scenario", orientation="h", text_auto=".1f", color_discrete_sequence=[BLUE])
        fig.update_layout(title="Scenario sensitivity", xaxis_range=[0, 100])
        st.plotly_chart(style_figure(fig, 350), width="stretch", config={"displayModeBar": False})

    benchmark = country_latest[["Indicator label", "Need Score", "Pillar"]].copy()
    global_median = scored_latest.groupby("Indicator ID", observed=True)["Need Score"].median()
    region_iso = scored.loc[scored["Region"].eq(selected["Region"]), "ISO3"]
    region_median = scored_latest.loc[scored_latest["ISO3"].isin(region_iso)].groupby("Indicator ID", observed=True)["Need Score"].median()
    benchmark["Global median"] = country_latest["Indicator ID"].map(global_median)
    benchmark["Regional median"] = country_latest["Indicator ID"].map(region_median)
    long = benchmark.melt(id_vars=["Indicator label", "Pillar"], var_name="Series", value_name="Score")
    fig = px.bar(
        long,
        x="Score",
        y="Indicator label",
        color="Series",
        barmode="group",
        orientation="h",
        color_discrete_map={"Need Score": TEAL, "Global median": "#B8C6CF", "Regional median": "#203A4C"},
    )
    fig.update_layout(title="Indicator need scores versus benchmarks", xaxis_range=[0, 100], legend_title=None)
    st.plotly_chart(style_figure(fig, 560), width="stretch", config={"displayModeBar": False})

    indicator = st.selectbox("Historical indicator", country_latest["Indicator ID"].tolist(), format_func=lambda value: LABELS[value])
    trend = history.loc[(history["ISO3"].eq(selected["ISO3"])) & (history["Indicator ID"].eq(indicator))].sort_values("Year")
    fig = px.line(trend, x="Year", y="Value", markers=True, color_discrete_sequence=[GREEN])
    fig.update_layout(title=f"{LABELS[indicator]} history", xaxis_dtick=1, yaxis_title=trend["Unit"].dropna().iloc[0] if trend["Unit"].notna().any() else None)
    st.plotly_chart(style_figure(fig, 330), width="stretch", config={"displayModeBar": False})

    display = country_latest[["Indicator label", "Pillar", "Value", "Year", "Need Score", "Direction", "Within-Pillar Weight", "DataAge", "Status"]].rename(
        columns={"Value": "Raw value", "Year": "Observation year", "Within-Pillar Weight": "Pillar weight", "DataAge": "Data age"}
    )
    st.dataframe(display, width="stretch", hide_index=True)
    missing = int((display["Status"] == "Missing").sum())
    stale = int((display["Status"] == "Stale").sum())
    st.caption(f"{missing} missing indicator(s); {stale} stale observation(s) at the selected {context['stale_years']}-year threshold.")
