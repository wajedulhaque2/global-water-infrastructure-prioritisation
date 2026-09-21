from __future__ import annotations

import pandas as pd
import plotly.express as px
import streamlit as st

from chart_utils import BLUE, GREEN, ORANGE, TEAL, horizontal_bar, style_figure


def render(scored, latest, indicators, context: dict[str, object]) -> None:
    st.title("Data quality")
    st.caption("Coverage, freshness, and eligibility diagnostics")

    analysis_end = context["analysis_end_year"]
    latest = latest.copy()
    latest["Data age"] = analysis_end - pd.to_numeric(latest["Year"], errors="coerce")
    latest["Freshness"] = "Current"
    latest.loc[latest["Data age"] >= context["stale_years"], "Freshness"] = "Stale"

    cols = st.columns(4)
    cols[0].metric("Countries in source", f"{scored['ISO3'].nunique():,}")
    cols[1].metric("Eligible countries", f"{scored['Priority Score'].notna().sum():,}")
    cols[2].metric("Latest observations", f"{len(latest):,}")
    cols[3].metric("Stale observations", f"{(latest['Freshness'] == 'Stale').sum():,}")

    coverage = latest.groupby(["Indicator ID", "Indicator"], observed=True).agg(
        countries=("ISO3", "nunique"),
        latest_year=("Year", "max"),
        stale=("Freshness", lambda values: int((values == "Stale").sum())),
    ).reset_index()
    coverage["Coverage"] = coverage["countries"] / scored["ISO3"].nunique()

    left, right = st.columns(2)
    with left:
        coverage_fig = horizontal_bar(coverage, "Coverage", "Indicator", "Country coverage by indicator", TEAL, 480)
        coverage_fig.update_xaxes(tickformat=".0%", range=[0, 1])
        st.plotly_chart(coverage_fig, width="stretch", config={"displayModeBar": False})
    with right:
        completeness = px.histogram(scored, x="Completeness", nbins=10, color_discrete_sequence=[BLUE])
        completeness.add_vline(x=context["min_completeness"], line_dash="dash", line_color=ORANGE)
        completeness.update_layout(title="Country completeness distribution", xaxis_tickformat=".0%", yaxis_title="Countries")
        st.plotly_chart(style_figure(completeness, 480), width="stretch", config={"displayModeBar": False})

    stale_by_indicator = coverage.loc[coverage["stale"] > 0].sort_values("stale", ascending=False)
    if stale_by_indicator.empty:
        st.success(f"No latest observations are stale at the {context['stale_years']}-year threshold.")
    else:
        st.plotly_chart(horizontal_bar(stale_by_indicator, "stale", "Indicator", "Stale latest observations by indicator", ORANGE, 380), width="stretch", config={"displayModeBar": False})

    st.subheader("Indicator coverage")
    st.dataframe(
        coverage[["Indicator", "countries", "Coverage", "latest_year", "stale"]].rename(
            columns={"countries": "Countries", "latest_year": "Latest year", "stale": "Stale observations"}
        ),
        width="stretch",
        hide_index=True,
    )

    with st.expander("Countries below the completeness threshold"):
        excluded = scored.loc[scored["Priority Score"].isna(), ["Country", "Region", "IncomeLevel", "Available Indicators", "Completeness"]]
        st.dataframe(excluded.sort_values(["Completeness", "Country"]), width="stretch", hide_index=True)
