from decimal import Decimal

from report.export_reports import export_monthly_report


def test_export_monthly_report_labels_pit_as_business_pit(tmp_path):
    out_file = tmp_path / "report_monthly.csv"

    export_monthly_report(
        monthly_jpk={
            "2026-01": {
                "sales_net": Decimal("1000.00"),
                "purchase_net": Decimal("100.00"),
                "sales_vat": Decimal("230.00"),
                "purchase_vat": Decimal("23.00"),
            }
        },
        delegations_monthly={},
        other_costs_monthly={},
        pit_monthly={
            "2026-01": {
                "income_cumulative": Decimal("900.00"),
                "pit_cumulative": Decimal("0.00"),
                "pit_payment": Decimal("0.00"),
            }
        },
        out_file=out_file,
    )

    header = out_file.read_text(encoding="utf-8-sig").splitlines()[0]

    assert "Dochód JDG narastająco" in header
    assert "PIT JDG narastająco" in header
    assert "Zaliczka PIT JDG" in header
