from decimal import Decimal

from other_costs import load_other_costs, sum_other_costs_by_month


def test_load_other_costs_valid_csv(tmp_path):
    csv_path = tmp_path / "other_costs.csv"
    csv_path.write_text(
        "\n".join(
            [
                "date;type;description;amount_pln",
                "2026-01-10;insurance;OC działalności;300.00",
                "2026-01-20;bank;Opłata bankowa;50,50",
                "2026-02-10;software;Abonament;200.00",
            ]
        ),
        encoding="utf-8",
    )

    costs = load_other_costs(csv_path)

    assert len(costs) == 3

    assert costs[0]["date"] == "2026-01-10"
    assert costs[0]["month"] == "2026-01"
    assert costs[0]["type"] == "insurance"
    assert costs[0]["description"] == "OC działalności"
    assert costs[0]["amount_pln"] == Decimal("300.00")

    assert costs[1]["amount_pln"] == Decimal("50.50")


def test_sum_other_costs_by_month():
    costs = [
        {
            "date": "2026-01-10",
            "month": "2026-01",
            "type": "insurance",
            "description": "OC",
            "amount_pln": Decimal("300.00"),
        },
        {
            "date": "2026-01-20",
            "month": "2026-01",
            "type": "bank",
            "description": "Bank",
            "amount_pln": Decimal("50.00"),
        },
        {
            "date": "2026-02-10",
            "month": "2026-02",
            "type": "software",
            "description": "Abonament",
            "amount_pln": Decimal("200.00"),
        },
    ]

    monthly = sum_other_costs_by_month(costs)

    assert monthly["2026-01"] == Decimal("350.00")
    assert monthly["2026-02"] == Decimal("200.00")


def test_load_other_costs_missing_file(tmp_path):
    csv_path = tmp_path / "missing.csv"

    costs = load_other_costs(csv_path)

    assert costs == []
