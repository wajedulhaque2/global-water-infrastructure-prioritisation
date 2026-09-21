from __future__ import annotations

import sys
import unittest
from pathlib import Path

import pandas as pd


sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "dashboard"))

from data_loader import load_snapshot  # noqa: E402
from model import SCENARIOS, freshness_status, score_countries  # noqa: E402


class ModelTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.data = load_snapshot()
        cls.scored, cls.latest = score_countries(
            cls.data["latest"],
            cls.data["countries"],
            cls.data["indicators"],
            SCENARIOS["Water-Stress Focus"],
            0.75,
        )

    def test_source_snapshot_counts(self) -> None:
        self.assertEqual(len(self.data["history"]), 12_560)
        self.assertEqual(len(self.data["latest"]), 1_768)
        self.assertEqual(self.data["latest"]["Indicator ID"].nunique(), 9)
        self.assertEqual(self.data["countries"]["ISO3"].nunique(), 217)

    def test_water_stress_scenario_reconciles_to_workbook(self) -> None:
        eligible = self.scored.dropna(subset=["Priority Score"])
        self.assertEqual(len(eligible), 195)
        self.assertEqual(eligible.iloc[0]["Country"], "Niger")
        self.assertAlmostEqual(eligible.iloc[0]["Priority Score"], 92.98, places=1)
        rwanda = self.scored.loc[self.scored["Country"].eq("Rwanda")].iloc[0]
        self.assertAlmostEqual(rwanda["Priority Score"], 80.34, places=1)

    def test_missing_indicator_is_not_stale(self) -> None:
        missing = pd.Series({"Value": None, "Year": None})
        self.assertEqual(freshness_status(missing, 5, 2025), "Missing")

    def test_scores_remain_bounded(self) -> None:
        eligible = self.scored["Priority Score"].dropna()
        self.assertTrue(eligible.between(0, 100).all())


if __name__ == "__main__":
    unittest.main()
