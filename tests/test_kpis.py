import json
import tempfile
import unittest
from pathlib import Path

from src.kpi_tracker import KPITrackerCoordinator


class KPITests(unittest.TestCase):
    def test_scorecard_and_alert(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            (root / "shipments.csv").write_text(
                "shipment_id,provider,ship_date,delivery_date,promised_date,order_accurate,damage_free,exception,cost\n"
                "S1,ExampleCarrier Test,2026-01-01,2026-01-03,2026-01-02,1,1,1,100\n"
                "S2,ExampleCarrier Test,2026-01-02,2026-01-03,2026-01-04,1,0,0,120\n",
                encoding="utf-8",
            )
            targets = {
                "minimum_on_time_delivery_pct": 95,
                "minimum_order_accuracy_pct": 98,
                "minimum_damage_free_pct": 99,
                "maximum_exception_pct": 5,
                "maximum_avg_transit_days": 4,
                "maximum_avg_cost_per_shipment": 200,
            }
            (root / "targets.json").write_text(json.dumps(targets), encoding="utf-8")
            result = KPITrackerCoordinator().run(root / "shipments.csv", root / "targets.json")
            self.assertEqual(result["scorecards"][0]["shipments"], 2)
            self.assertEqual(result["scorecards"][0]["on_time_delivery_pct"], 50.0)
            self.assertTrue(any(a["metric"] == "on_time_delivery_pct" for a in result["alerts"]))


if __name__ == "__main__":
    unittest.main()
