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
        title={"font": {"size": 18}, "x": 0.025, "xanchor": "left"},
        margin={"l": 24, "r": 32, "t": 64, "b": 48},
        height=height,
        hoverlabel={"font": {"family": "Arial"}},
        bargap=0.3,
    )
    fig.update_xaxes(gridcolor="#E5EBEF", zeroline=False)
    fig.update_yaxes(gridcolor="#E5EBEF", zeroline=False)
    return fig


def horizontal_bar(
    frame, x: str, y: str, title: str, color: str = TEAL, height: int = 480,
    *, value_format: str = ".1f", maximum: float | None = None,
) -> go.Figure:
    ordered = frame.sort_values(x, ascending=True)
    fig = px.bar(ordered, x=x, y=y, orientation="h")
    fig.update_traces(
        marker_color=color,
        texttemplate=f"%{{x:{value_format}}}",
        textposition="outside",
        textfont={"size": 12, "color": NAVY},
        cliponaxis=False,
        hovertemplate=f"%{{y}}<br>%{{x:{value_format}}}<extra></extra>",
    )
    fig.update_layout(title=title, showlegend=False, uniformtext_minsize=11)
    fig.update_yaxes(title=None, showgrid=False, automargin=True, tickfont={"size": 12})
    fig.update_xaxes(title=None, rangemode="tozero", ticksuffix="", tickfont={"size": 11})
    if maximum is not None:
        fig.update_xaxes(range=[0, maximum * 1.1], tickvals=[0, maximum / 4, maximum / 2, maximum * 3 / 4, maximum])
    return style_figure(fig, height)
