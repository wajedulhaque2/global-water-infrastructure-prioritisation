from __future__ import annotations

import plotly.express as px
import plotly.graph_objects as go


NAVY = "#102A3A"
TEAL = "#087F8C"
BLUE = "#2F6690"
GREEN = "#2F7D4A"
ORANGE = "#D57A0B"
LIGHT = "#E8F0F5"
PILLAR_COLORS = {
    "Water Need": TEAL,
    "Human Development": "#2A9D8F",
    "Infrastructure & Affordability": "#5C7F7A",
    "Reach & Growth": GREEN,
}


def style_figure(fig: go.Figure, height: int | None = None) -> go.Figure:
    fig.update_layout(
        template="plotly_white",
        font={"family": "Arial", "color": NAVY},
        title={"font": {"size": 18}},
        margin={"l": 16, "r": 16, "t": 56, "b": 24},
        height=height,
        hoverlabel={"font": {"family": "Arial"}},
    )
    fig.update_xaxes(gridcolor="#E5EBEF", zeroline=False)
    fig.update_yaxes(gridcolor="#E5EBEF", zeroline=False)
    return fig


def horizontal_bar(frame, x: str, y: str, title: str, color: str = TEAL, height: int = 480) -> go.Figure:
    ordered = frame.sort_values(x, ascending=True)
    fig = px.bar(ordered, x=x, y=y, orientation="h", text_auto=".1f")
    fig.update_traces(marker_color=color, hovertemplate=f"%{{y}}<br>%{{x:,.1f}}<extra></extra>")
    fig.update_layout(title=title, showlegend=False)
    return style_figure(fig, height)
