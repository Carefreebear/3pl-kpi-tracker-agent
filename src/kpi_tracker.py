"""Agentic 3PL KPI scorecard workflow."""

from __future__ import annotations

import argparse
import csv
import json
from collections import defaultdict
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from statistics import mean
from typing import Any


@dataclass(frozen=True)
class Shipment:
    shipment_id: str
    provider: str
    ship_date: str
    delivery_date: str
    promised_date: str
    order_accurate: bool
    damage_free: bool
    exception: bool
    cost: float

    @property
    def on_time(self) -> bool:
        return self.delivery_date <= self.promised_date

    @property
    def transit_days(self) -> int:
        start = datetime.strptime(self.ship_date, "%Y-%m-%d").date()
        end = datetime.strptime(self.delivery_date, "%Y-%m-%d").date()
        return (end - start).days


@dataclass(frozen=True)
class ProviderScorecard:
    provider: str
    shipments: int
    on_time_delivery_pct: float
    order_accuracy_pct: float
    damage_free_pct: float
    exception_pct: float
    avg_transit_days: float
    avg_cost_per_shipment: float


class DataQualityAgent:
    role = "Data Quality Agent"

    def load(self, path: Path) -> tuple[list[Shipment], dict[str, Any]]:
        shipments: list[Shipment] = []
        with path.open(newline="", encoding="utf-8") as handle:
            for row in csv.DictReader(handle):
                shipment = Shipment(
                    shipment_id=row["shipment_id"].strip(),
                    provider=row["provider"].strip(),
                    ship_date=row["ship_date"],
                    delivery_date=row["delivery_date"],
                    promised_date=row["promised_date"],
                    order_accurate=row["order_accurate"] == "1",
                    damage_free=row["damage_free"] == "1",
                    exception=row["exception"] == "1",
                    cost=float(row["cost"]),
                )
                if shipment.transit_days < 0 or shipment.cost < 0:
                    raise ValueError(f"Invalid shipment values for {shipment.shipment_id}")
                shipments.append(shipment)
        if not shipments:
            raise ValueError("No shipments found")
        if len({s.shipment_id for s in shipments}) != len(shipments):
            raise ValueError("Shipment IDs must be unique")
        return shipments, {"agent": self.role, "event": "shipments_validated", "count": len(shipments)}


class KPIAgent:
    role = "KPI Agent"

    @staticmethod
    def _pct(values: list[bool]) -> float:
        return round(sum(values) / len(values) * 100, 1)

    def calculate(self, shipments: list[Shipment]) -> tuple[list[ProviderScorecard], dict[str, Any]]:
        groups: dict[str, list[Shipment]] = defaultdict(list)
        for shipment in shipments:
            groups[shipment.provider].append(shipment)
        scorecards = []
        for provider, rows in sorted(groups.items()):
            scorecards.append(ProviderScorecard(
                provider=provider,
                shipments=len(rows),
                on_time_delivery_pct=self._pct([s.on_time for s in rows]),
                order_accuracy_pct=self._pct([s.order_accurate for s in rows]),
                damage_free_pct=self._pct([s.damage_free for s in rows]),
                exception_pct=self._pct([s.exception for s in rows]),
                avg_transit_days=round(mean(s.transit_days for s in rows), 1),
                avg_cost_per_shipment=round(mean(s.cost for s in rows), 2),
            ))
        return scorecards, {"agent": self.role, "event": "kpis_calculated", "providers": len(scorecards)}


class PerformanceAlertAgent:
    role = "Performance Alert Agent"

    def evaluate(self, scorecards: list[ProviderScorecard], targets: dict[str, float]) -> tuple[list[dict[str, Any]], dict[str, Any]]:
        alerts: list[dict[str, Any]] = []
        minimums = {
            "on_time_delivery_pct": targets["minimum_on_time_delivery_pct"],
            "order_accuracy_pct": targets["minimum_order_accuracy_pct"],
            "damage_free_pct": targets["minimum_damage_free_pct"],
        }
        maximums = {
            "exception_pct": targets["maximum_exception_pct"],
            "avg_transit_days": targets["maximum_avg_transit_days"],
            "avg_cost_per_shipment": targets["maximum_avg_cost_per_shipment"],
        }
        for card in scorecards:
            for metric, target in minimums.items():
                actual = getattr(card, metric)
                if actual < target:
                    alerts.append({"provider": card.provider, "metric": metric, "actual": actual, "target": target, "severity": "high"})
            for metric, target in maximums.items():
                actual = getattr(card, metric)
                if actual > target:
                    alerts.append({"provider": card.provider, "metric": metric, "actual": actual, "target": target, "severity": "warning"})
        return alerts, {"agent": self.role, "event": "targets_evaluated", "alert_count": len(alerts)}


class KPITrackerCoordinator:
    def run(self, shipments_path: Path, targets_path: Path) -> dict[str, Any]:
        trace: list[dict[str, Any]] = []
        shipments, event = DataQualityAgent().load(shipments_path)
        trace.append(event)
        scorecards, event = KPIAgent().calculate(shipments)
        trace.append(event)
        targets = json.loads(targets_path.read_text(encoding="utf-8"))
        alerts, event = PerformanceAlertAgent().evaluate(scorecards, targets)
        trace.append(event)
        return {"scorecards": [asdict(card) for card in scorecards], "alerts": alerts, "trace": trace}


def main() -> None:
    parser = argparse.ArgumentParser(description="Calculate and evaluate 3PL KPIs")
    parser.add_argument("--shipments", type=Path, required=True)
    parser.add_argument("--targets", type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(KPITrackerCoordinator().run(args.shipments, args.targets), indent=2))


if __name__ == "__main__":
    main()
