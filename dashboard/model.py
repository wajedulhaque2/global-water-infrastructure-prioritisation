from __future__ import annotations

import numpy as np
import pandas as pd


PILLARS = [
    "Water Need",
    "Human Development",
    "Infrastructure & Affordability",
    "Reach & Growth",
]

SCENARIOS = {
    "Base Case": {
        "Water Need": 0.40,
        "Human Development": 0.20,
        "Infrastructure & Affordability": 0.20,
        "Reach & Growth": 0.20,
    },
    "Water-Stress Focus": {
        "Water Need": 0.60,
        "Human Development": 0.15,
        "Infrastructure & Affordability": 0.10,
        "Reach & Growth": 0.15,
    },
    "Social-Impact Focus": {
        "Water Need": 0.25,
        "Human Development": 0.35,
        "Infrastructure & Affordability": 0.15,
        "Reach & Growth": 0.25,
    },
}


def normalize_weights(weights: dict[str, float]) -> dict[str, float]:
    total = sum(max(float(weights.get(pillar, 0)), 0) for pillar in PILLARS)
    if total <= 0:
        return SCENARIOS["Base Case"].copy()
    return {pillar: max(float(weights.get(pillar, 0)), 0) / total for pillar in PILLARS}


def add_need_scores(latest: pd.DataFrame) -> pd.DataFrame:
    result = latest.copy()
    result["Value"] = pd.to_numeric(result["Value"], errors="coerce")
    result["Need Score"] = np.nan
    for _, group in result.groupby("Indicator ID", observed=True):
        values = group["Value"].dropna()
        if len(values) <= 1:
            percentile = pd.Series(0.5, index=values.index)
        else:
            percentile = (values.rank(method="min") - 1) / (len(values) - 1)
        if group["Direction"].iloc[0] == "LOW":
            percentile = 1 - percentile
        result.loc[values.index, "Need Score"] = (percentile * 100).round(1)
    return result


def score_countries(
    latest: pd.DataFrame,
    countries: pd.DataFrame,
    indicator_map: pd.DataFrame,
    scenario_weights: dict[str, float],
    min_completeness: float = 0.75,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    scored_latest = add_need_scores(latest)
    active = indicator_map.loc[indicator_map["Active"].eq("Yes")].copy()
    active["Within-Pillar Weight"] = pd.to_numeric(active["Within-Pillar Weight"], errors="coerce")
    active_weights = active.set_index("Indicator ID")["Within-Pillar Weight"].to_dict()
    active_indicators = active["Indicator ID"].tolist()

    scores = scored_latest.pivot(index="ISO3", columns="Indicator ID", values="Need Score")
    scores = scores.reindex(columns=active_indicators)
    output = countries[["ISO3", "Country", "Region", "IncomeLevel", "Longitude", "Latitude"]].copy()
    output = output.set_index("ISO3")
    output["Available Indicators"] = scores.notna().sum(axis=1)
    output["Completeness"] = output["Available Indicators"] / len(active_indicators)

    for pillar in PILLARS:
        indicator_ids = active.loc[active["Pillar"].eq(pillar), "Indicator ID"].tolist()
        numerator = sum(scores[indicator].fillna(0) * active_weights[indicator] for indicator in indicator_ids)
        denominator = sum(scores[indicator].notna() * active_weights[indicator] for indicator in indicator_ids)
        output[pillar] = numerator / denominator.where(denominator > 0)

    normalized = normalize_weights(scenario_weights)
    numerator = sum(output[pillar].fillna(0) * normalized[pillar] for pillar in PILLARS)
    denominator = sum(output[pillar].notna() * normalized[pillar] for pillar in PILLARS)
    output["Priority Score"] = (numerator / denominator.where(denominator > 0)).where(
        output["Completeness"] >= min_completeness
    )
    output["Eligibility"] = np.where(output["Priority Score"].notna(), "Eligible", "Insufficient data")
    output["Rank"] = output["Priority Score"].rank(method="min", ascending=False).astype("Int64")
    output = output.reset_index().sort_values(["Priority Score", "Country"], ascending=[False, True], na_position="last")
    return output, scored_latest


def scenario_comparison(
    latest: pd.DataFrame,
    countries: pd.DataFrame,
    indicators: pd.DataFrame,
    custom_weights: dict[str, float],
    min_completeness: float,
) -> pd.DataFrame:
    frames = []
    for scenario, weights in {**SCENARIOS, "Custom": custom_weights}.items():
        scored, _ = score_countries(latest, countries, indicators, weights, min_completeness)
        frames.append(scored[["ISO3", "Country", "Region", "IncomeLevel", "Priority Score", "Rank"]].assign(Scenario=scenario))
    return pd.concat(frames, ignore_index=True)


def freshness_status(row: pd.Series, stale_years: int, analysis_end_year: int) -> str:
    if pd.isna(row.get("Value")) or pd.isna(row.get("Year")):
        return "Missing"
    return "Stale" if analysis_end_year - int(row["Year"]) >= stale_years else "Current"
