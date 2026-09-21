from __future__ import annotations

import unittest
from pathlib import Path

from streamlit.testing.v1 import AppTest


APP = Path(__file__).resolve().parents[1] / "dashboard" / "app.py"


class DashboardSmokeTest(unittest.TestCase):
    def test_every_view_renders_without_exception(self) -> None:
        app = AppTest.from_file(str(APP), default_timeout=20).run()
        self.assertFalse(app.exception)
        for view in ["Country explorer", "Scenario comparison", "Data quality", "Methodology"]:
            app.radio[0].set_value(view).run()
            self.assertFalse(app.exception, view)

    def test_scenario_and_country_filters_update(self) -> None:
        app = AppTest.from_file(str(APP), default_timeout=20).run()
        self.assertEqual(app.metric[2].value, "93.0")
        app.selectbox[0].set_value("Base Case").run()
        self.assertFalse(app.exception)
        self.assertEqual(app.metric[2].value, "93.7")
        app.radio[0].set_value("Country explorer").run()
        country_select = next(widget for widget in app.selectbox if widget.label == "Country")
        country_select.set_value("Niger").run()
        self.assertFalse(app.exception)
        self.assertEqual(app.metric[0].value, "1")


if __name__ == "__main__":
    unittest.main()
