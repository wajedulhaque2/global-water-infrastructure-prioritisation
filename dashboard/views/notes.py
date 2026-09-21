from __future__ import annotations

import streamlit as st


def render(metadata: dict[str, object]) -> None:
    st.title("Methodology and data notes")
    st.markdown(
        """
### What the score means

Each indicator is converted to a 0–100 relative need score using its percentile position across countries with available data. Direction is reversed for indicators where lower raw values imply greater need. Indicator scores are combined into four pillars, then pillar scores are combined using the selected scenario weights.

Missing indicators are not treated as zero. Available weights are renormalized within each pillar, and countries below the selected completeness threshold do not receive a final priority score.

### Interpretation

The result is a screening and prioritisation measure, not an investment recommendation. It does not include project costs, political risk, implementation capacity, engineering constraints, subnational variation, or expected financial return.

### Source

World Bank World Development Indicators, using the workbook's embedded Power Query snapshot.
"""
    )
    st.write(f"**Source coverage:** {metadata['analysis_start_year']}–{metadata['analysis_end_year']}")
    st.write(f"**Retrieved:** {metadata['retrieved_at']}")
    st.write(f"**Historical observations:** {metadata['history_rows']:,}")
    st.write(f"**Latest observations:** {metadata['latest_rows']:,}")
    st.link_button("Open World Bank Indicators", metadata["source_url"])
