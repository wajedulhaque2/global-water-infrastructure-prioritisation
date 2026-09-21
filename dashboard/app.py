from __future__ import annotations

from pathlib import Path

import streamlit as st

from data_loader import load_snapshot
from model import PILLARS, SCENARIOS, scenario_comparison, score_countries
from views import country, data_quality, executive, notes, scenarios


st.set_page_config(page_title="Global water priorities", page_icon="💧", layout="wide")
css_path = Path(__file__).resolve().parent / "assets" / "style.css"
st.markdown(f"<style>{css_path.read_text(encoding='utf-8')}</style>", unsafe_allow_html=True)

data = load_snapshot()
metadata = data["metadata"]

st.sidebar.markdown('<div class="brand-title">Global water priorities</div>', unsafe_allow_html=True)
st.sidebar.caption("Source-backed interactive dashboard")
view = st.sidebar.radio(
    "View",
    ["Executive dashboard", "Country explorer", "Scenario comparison", "Data quality", "Methodology"],
)
st.sidebar.divider()
st.sidebar.caption("Data provided by the World Bank")

scenario = st.sidebar.selectbox("Scenario", [*SCENARIOS, "Custom"], index=1)
custom_weights = SCENARIOS.get(scenario, SCENARIOS["Base Case"]).copy()
if scenario == "Custom":
    st.sidebar.markdown("**Custom pillar weights**")
    custom_weights = {}
    for pillar in PILLARS:
        custom_weights[pillar] = st.sidebar.slider(
            pillar,
            min_value=0,
            max_value=100,
            value=int(SCENARIOS["Base Case"][pillar] * 100),
            step=5,
            key=f"custom_{pillar}",
        ) / 100
    st.sidebar.caption("Weights are normalized to 100% in the calculation.")

min_completeness = st.sidebar.slider("Minimum data completeness", 0.50, 1.00, 0.75, 0.05)
stale_years = st.sidebar.slider("Stale-data threshold (years)", 1, 10, 5)

scored, scored_latest = score_countries(
    data["latest"],
    data["countries"],
    data["indicators"],
    custom_weights,
    min_completeness,
)
comparison = scenario_comparison(
    data["latest"],
    data["countries"],
    data["indicators"],
    custom_weights,
    min_completeness,
)

regions = ["All regions"] + sorted(scored["Region"].dropna().unique().tolist())
incomes = ["All income levels"] + sorted(scored["IncomeLevel"].dropna().unique().tolist())
region = st.sidebar.selectbox("Region", regions)
income = st.sidebar.selectbox("Income level", incomes)

country_scope = scored.copy()
if region != "All regions":
    country_scope = country_scope.loc[country_scope["Region"].eq(region)]
if income != "All income levels":
    country_scope = country_scope.loc[country_scope["IncomeLevel"].eq(income)]
country_options = sorted(country_scope["Country"].dropna().tolist()) or sorted(scored["Country"].dropna().tolist())
default_country = country_options.index("Rwanda") if "Rwanda" in country_options else 0
selected_country = st.sidebar.selectbox("Country", country_options, index=default_country)

context = {
    "scenario": scenario,
    "weights": custom_weights,
    "min_completeness": min_completeness,
    "stale_years": stale_years,
    "region": region,
    "income": income,
    "country": selected_country,
    "analysis_end_year": int(metadata["analysis_end_year"]),
}

if view == "Executive dashboard":
    executive.render(scored, scored_latest, context)
elif view == "Country explorer":
    country.render(scored, scored_latest, data["history"], data["indicators"], comparison, context)
elif view == "Scenario comparison":
    scenarios.render(comparison, context)
elif view == "Data quality":
    data_quality.render(scored, data["latest"], data["indicators"], context)
else:
    notes.render(metadata)
