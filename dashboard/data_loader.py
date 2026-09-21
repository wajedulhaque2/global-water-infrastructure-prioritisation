from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path

import pandas as pd


DATA_DIR = Path(__file__).resolve().parent / "data"


@lru_cache(maxsize=1)
def load_snapshot() -> dict[str, object]:
    countries = pd.read_csv(DATA_DIR / "countries.csv")
    history = pd.read_csv(
        DATA_DIR / "indicator_history.csv",
        parse_dates=["SourceLastUpdated", "RetrievedAt"],
    )
    latest = pd.read_csv(
        DATA_DIR / "latest_indicators.csv",
        parse_dates=["SourceLastUpdated", "RetrievedAt"],
    )
    indicators = pd.read_csv(DATA_DIR / "indicator_map.csv")
    metadata = json.loads((DATA_DIR / "metadata.json").read_text(encoding="utf-8"))
    return {
        "countries": countries,
        "history": history,
        "latest": latest,
        "indicators": indicators,
        "metadata": metadata,
    }
