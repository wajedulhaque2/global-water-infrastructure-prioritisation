from __future__ import annotations

import pandas as pd
import plotly.express as px
import streamlit as st

from chart_utils import BLUE, ORANGE, TEAL, horizontal_bar, style_figure


def render(comparison, context: dict[str, object]) -> None:
    st.title("Scenario comparison")
    st.caption("How country priorities change when pillar weights change")

    selected_name = context["scenario"] if context["scenario"] != "Custom" else "Custom"
    selected = comparison.loc[comparison["Scenario"].eq(selected_name)].copy()
    base = comparison.loc[comparison["Scenario"].eq("Base Case"), ["ISO3", "Priority Score", "Rank"]].rename(
        columns={"Priority Score": "Base score", "Rank": "Base rank"}
    )
    merged = selected.merge(base, on="ISO3", how="left")
    merged["Score change"] = merged["Priority Score"] - merged["Base score"]
    merged["Rank improvement"] = merged["Base rank"] - merged["Rank"]

    cols = st.columns(3)
    cols[0].metric("Countries compared", f"{merged['Priority Score'].notna().sum():,}")
    cols[1].metric("Largest score increase", f"{merged['Score change'].max():+.1f}")
    cols[2].metric("Largest score decrease", f"{merged['Score change'].min():+.1f}")

    left, right = st.columns(2)
    with left:
        top = merged.dropna(subset=["Priority Score"]).sort_values("Priority Score", ascending=False).head(15)
        st.plotly_chart(horizontal_bar(top, "Priority Score", "Country", f"Top countries — {selected_name}", TEAL, 520), width="stretch", config={"displayModeBar": False})
    with right:
        movers = merged.dropna(subset=["Score change"]).assign(abs_change=lambda x: x["Score change"].abs()).nlargest(15, "abs_change")
        movers = movers.sort_values("Score change")
        fig = px.bar(
            movers,
            x="Score change",
            y="Country",
            orientation="h",
            color="Score change",
            color_continuous_scale=[[0, "#2F6690"], [0.5, "#D9E2E8"], [1, ORANGE]],
            color_continuous_midpoint=0,
            text_auto="+.1f",
        )
        fig.update_layout(title="Largest score changes versus Base Case", coloraxis_showscale=False)
        st.plotly_chart(style_figure(fig, 520), width="stretch", config={"displayModeBar": False})

    scatter = merged.dropna(subset=["Base score", "Priority Score"])
    fig = px.scatter(
        scatter,
        x="Base score",
        y="Priority Score",
        color="Region",
        hover_name="Country",
        hover_data={"Rank": True, "Rank improvement": True},
    )
    fig.add_shape(type="line", x0=0, y0=0, x1=100, y1=100, line={"color": "#8AA0AD", "dash": "dash"})
    fig.update_layout(title=f"Base Case versus {selected_name}", xaxis_range=[0, 100], yaxis_range=[0, 100])
    st.plotly_chart(style_figure(fig, 560), width="stretch", config={"displayModeBar": False})

    st.dataframe(
        merged[["Rank", "Country", "Region", "Priority Score", "Base score", "Score change", "Rank improvement"]].sort_values("Rank"),
        width="stretch",
        hide_index=True,
    )
