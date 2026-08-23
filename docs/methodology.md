# Methodology

## Purpose

The Global Water Infrastructure Prioritisation model is a country-level screening tool designed to identify locations that may merit further investigation for water-infrastructure investment. It combines World Bank development indicators into transparent 0–100 Need Scores, four thematic pillar scores, and a weighted Priority Score.

The model is designed for relative prioritisation. It is **not** an automatic investment recommendation, engineering feasibility study, financial valuation, or forecast.

## Data source and processing

The model retrieves country metadata and development indicators from the **World Bank Indicators API** using Power Query.

The data pipeline is:

```text
World Bank Indicators API
        ↓
qryCountryMaster
        ↓
fnGetWBIndicator
        ↓
qryIndicatorData
        ↓
qryLatestIndicators
        ↓
qryScoringBase
        ↓
Scoring layer
        ↓
Dashboard / Country Detail / Methodology
```

### Power Query components

- **`qryCountryMaster`** — retrieves country metadata and removes World Bank aggregate regions and income groups.
- **`fnGetWBIndicator`** — reusable Power Query function for retrieving an indicator across the configured analysis period.
- **`qryIndicatorData`** — combines the historical indicator series into long-format country × indicator × year data.
- **`qryLatestIndicators`** — removes null analytical observations, selects the latest valid observation per country × indicator, preserves the actual observation year, and calculates data-age / stale-data fields.
- **`qryScoringBase`** — pivots latest values and observation years into one row per country for the Excel scoring layer.

## Analysis window

The workbook exposes an **Earliest API Year** and **Latest API Year** in the Controls sheet. Indicators are not forced to a single year because World Bank series update at different frequencies.

For each country × indicator combination, the model uses the most recent non-null observation available within the configured analysis window.

## Indicator framework

| Pillar | Indicator | World Bank code | Direction | Within-pillar weight |
|---|---|---|---|---:|
| Water Need | People using safely managed drinking water services | `SH.H2O.SMDW.ZS` | LOW | 60% |
| Water Need | Renewable internal freshwater resources per capita | `ER.H2O.INTR.PC` | LOW | 40% |
| Human Development | Mortality rate, under-5 | `SH.DYN.MORT` | HIGH | 60% |
| Human Development | Primary completion rate, total | `SE.PRM.CMPT.ZS` | LOW | 40% |
| Infrastructure & Affordability | GDP per capita, PPP | `NY.GDP.PCAP.PP.CD` | LOW | 50% |
| Infrastructure & Affordability | Access to electricity | `EG.ELC.ACCS.ZS` | LOW | 50% |
| Reach & Growth | Rural population | `SP.RUR.TOTL.ZS` | HIGH | 30% |
| Reach & Growth | Population growth | `SP.POP.GROW` | HIGH | 30% |
| Reach & Growth | Total population | `SP.POP.TOTL` | HIGH | 40% |

### Scoring direction

- **HIGH**: higher raw values imply greater relative priority.
- **LOW**: lower raw values imply greater relative priority.

## Normalisation

Indicators use different units and scales, so raw values cannot be combined directly. The workbook converts each active indicator into a **0–100 Need Score** using its percentile position within the available country distribution.

The named Excel function is conceptually:

```excel
=LAMBDA(value,data,direction,
    LET(
        clean,FILTER(data,ISNUMBER(data)),
        pct,IFERROR(PERCENTRANK.INC(clean,value),""),
        IF(
            NOT(ISNUMBER(value)),
            "",
            IF(
                direction="HIGH",
                pct*100,
                IF(direction="LOW",(1-pct)*100,"")
            )
        )
    )
)
```

Interpretation:

- **0** = relatively low need within the available distribution.
- **100** = relatively high need within the available distribution.

Percentile normalisation was selected because it limits the influence of extreme values and provides a consistent relative scale across indicators with very different units and distributions.

## Pillar construction

Indicator Need Scores are combined within each pillar using the configured within-pillar weights.

If an indicator is unavailable for an otherwise eligible country, the missing observation is **not treated as zero**. The available indicator weights within the pillar are renormalised so that missing data does not mechanically penalise the country.

## Missing data and completeness

Country completeness is calculated as:

```text
Available active indicators / Total active indicators
```

The workbook applies a configurable **Minimum Completeness** threshold. Countries below that threshold do not receive a final Priority Score.

This separates two ideas:

- a country may have some usable data;
- but it must have sufficient overall coverage to be included in the final ranking.

## Data freshness

Because World Bank indicators update at different frequencies, the model tracks the age of each latest observation.

```text
Data Age = Analysis End Year − Observation Year
```

Observations at or above the configured stale-data threshold are flagged as **STALE**. Stale observations remain visible and are not automatically discarded; the purpose of the flag is transparency.

## Scenario framework

The four pillar scores are combined using scenario-specific weights.

| Scenario | Water Need | Human Development | Infrastructure & Affordability | Reach & Growth |
|---|---:|---:|---:|---:|
| Base Case | 40% | 20% | 20% | 20% |
| Water-Stress Focus | 60% | 15% | 10% | 15% |
| Social-Impact Focus | 25% | 35% | 15% | 25% |
| Custom | User-defined | User-defined | User-defined | User-defined |

The scenario framework is intended to make model assumptions explicit and test how sensitive the ranking is to different decision priorities.

## Overall Priority Score

For an eligible country, the Priority Score is the weighted average of the available pillar scores under the selected scenario.

Conceptually:

```text
Priority Score =
Σ(Pillar Score × Scenario Weight)
─────────────────────────────────
Σ(Available Pillar Weights)
```

If an entire pillar is unavailable, its weight is excluded from the denominator and the remaining pillar weights are renormalised.

Countries are ranked from highest to lowest Priority Score.

## Country-level diagnostics

The Country Detail sheet exposes the analytical components behind the final score:

- raw value;
- observation year;
- Need Score;
- HIGH / LOW direction;
- pillar assignment;
- within-pillar weight;
- data age and freshness;
- global median Need Score;
- regional median Need Score;
- 2018–2025 historical sparkline;
- pillar scores and contributions;
- scenario sensitivity;
- global rank and percentile.

The purpose of the drill-down is to make the model explainable rather than presenting a ranking without diagnostic context.

## Model QA

The workbook includes quality-assurance checks covering areas such as:

- scenario weights summing to 100%;
- Priority Scores remaining within the 0–100 range;
- duplicate latest-observation keys;
- active-indicator counts;
- model eligibility / completeness;
- consistency between calculated contributions and the final Priority Score.

## Interpretation

A high Priority Score means that a country ranks relatively high on the selected combination of water need, human-development vulnerability, infrastructure / affordability constraints, and population reach / growth.

It does **not** mean that a specific project is financially attractive, technically feasible, politically executable, or socially optimal.

## Limitations

1. **Relative scoring** — percentile scores depend on the available cross-country distribution and are not absolute thresholds.
2. **Country-level aggregation** — national averages can hide substantial subnational inequality and infrastructure gaps.
3. **Data availability** — some indicators have older or incomplete observations.
4. **Weight sensitivity** — final rankings depend on the selected scenario and within-pillar weights.
5. **No causal interpretation** — the model does not estimate the impact of infrastructure investment.
6. **No project economics** — capital cost, operating cost, financing structure, expected return, and project-level demand are outside scope.
7. **No implementation-risk model** — political risk, procurement capacity, institutional quality, conflict exposure, and delivery constraints are not modelled directly.

## Data source

Primary source: **World Bank World Development Indicators**.

- https://data.worldbank.org/indicator
- https://datahelpdesk.worldbank.org/knowledgebase/topics/125589-developer-information
