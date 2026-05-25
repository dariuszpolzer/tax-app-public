import csv
from collections import defaultdict
from decimal import Decimal
from pathlib import Path


def load_other_costs(path: str | Path):
    path = Path(path)

    if not path.exists():
        return []

    costs = []

    with open(path, encoding="utf-8-sig") as f:
        reader = csv.DictReader(f, delimiter=";")

        for row in reader:
            costs.append(
                {
                    "date": row["date"],
                    "month": row["date"][:7],
                    "type": row["type"],
                    "description": row["description"],
                    "amount_pln": Decimal(row["amount_pln"].replace(",", ".")),
                }
            )

    return costs


def sum_other_costs_by_month(costs):
    monthly = defaultdict(lambda: Decimal("0.00"))

    for cost in costs:
        monthly[cost["month"]] += cost["amount_pln"]

    return monthly
