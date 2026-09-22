from __future__ import annotations

import plotly.express as px
import pandas as pd
import streamlit as st

from chart_utils import BLUE, ORANGE, PILLAR_COLORS, TEAL, horizontal_bar, style_figure


def render(scored, latest, context: dict[str, object]) -> None:
    filtered = scored.copy()
    if context["region"] != "All regions":
        filtered = filtered.loc[filtered["Region"].eq(context["region"])]
    if context["income"] != "All income levels":
        filtered = filtered.loc[filtered["IncomeLevel"].eq(context["income"])]
    eligible = filtered.loc[filtered["Priority Score"].notna()].copy()

    st.title("Global water-infrastructure priorities")
    st.caption("Country screening based on World Bank development indicators")
    st.markdown(
        f'<div class="scope-note"><b>{context["scenario"]}</b> · Scores use global percentile benchmarks · '
        f'Minimum completeness <b>{context["min_completeness"]:.0%}</b></div>',
        unsafe_allow_html=True,
    )

    top = eligible.iloc[0] if not eligible.empty else None
    cols = st.columns(4)
    cols[0].metric("Eligible countries", f"{len(eligible):,}")
    cols[1].metric("Highest priority country", top["Country"] if top is not None else "n.a.")
    cols[2].metric("Highest priority score", f"{top['Priority Score']:.1f}" if top is not None else "n.a.")
    cols[3].metric("Median completeness", f"{eligible['Completeness'].median():.0%}" if not eligible.empty else "n.a.")

    map_fig = px.choropleth(
        eligible,
        locations="ISO3",
        color="Priority Score",
        hover_name="Country",
        hover_data={"Rank": True, "Completeness": ":.0%", "ISO3": False},
        color_continuous_scale=[[0, "#E5F0E9"], [0.5, ORANGE], [1, "#944734"]],
        range_color=(0, 100),
    )
    map_fig.update_geos(showframe=False, showcoastlines=True, coastlinecolor="#BCC9D2")
    map_fig.update_layout(title="Global priority map", coloraxis_colorbar_title="Priority score")
    st.plotly_chart(style_figure(map_fig, 520), width="stretch", config={"displayModeBar": False})

    st.plotly_chart(
        horizontal_bar(eligible.head(15), "Priority Score", "Country", "Top priority countries", TEAL, 560, maximum=100),
        width="stretch",
        config={"displayModeBar": False},
    )
    regional = eligible.groupby("Region", observed=True)["Priority Score"].mean().sort_values().reset_index()
    st.plotly_chart(
        horizontal_bar(regional, "Priority Score", "Region", "Average priority score by region", BLUE, 390, maximum=100),
        width="stretch",
        config={"displayModeBar": False},
    )

    selected = scored.loc[scored["Country"].eq(context["country"])].iloc[0]
    st.subheader(f"{selected['Country']} profile")
    profile_cols = st.columns([1, 1.3])
    with profile_cols[0]:
        metrics = st.columns(3)
        metrics[0].metric("Global rank", f"{int(selected['Rank']):,}" if pd.notna(selected["Rank"]) else "n.a.")
        metrics[1].metric("Priority score", f"{selected['Priority Score']:.1f}" if selected["Priority Score"] == selected["Priority Score"] else "n.a.")
        metrics[2].metric("Completeness", f"{selected['Completeness']:.0%}")
        st.write(f"**Region:** {selected['Region']}")
        st.write(f"**Income level:** {selected['IncomeLevel']}")
    with profile_cols[1]:
        pillar = selected[list(PILLAR_COLORS)].rename_axis("Pillar").reset_index(name="Score")
        pillar_fig = horizontal_bar(pillar, "Score", "Pillar", "Pillar scores", TEAL, 320, maximum=100)
        pillar_fig.update_traces(marker_color=[PILLAR_COLORS[name] for name in pillar.sort_values("Score")["Pillar"]])
        st.plotly_chart(pillar_fig, width="stretch", config={"displayModeBar": False})

    st.info("Priority scores are relative screening measures. They do not include project cost, engineering feasibility, political risk, or expected financial return.")
