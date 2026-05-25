from decimal import Decimal

from delegations_csv import export_delegations_csv, load_delegations_csv


def test_load_delegations_csv_reads_public_format(tmp_path):
    path = tmp_path / "delegations.csv"
    path.write_text(
        "number;date_from;date_to;year;city;description;transport;employee;amount_pln;test\n"
        "DEL/1/2026;2026-03-01;2026-03-25;2026;Brunsbuttel;Delegacja;auto;Jan Testowy;4915,98;false\n",
        encoding="utf-8",
    )

    trips = load_delegations_csv(path)

    assert len(trips) == 1
    assert trips[0].nr_del == "DEL/1/2026"
    assert trips[0].purpose_city == "Brunsbuttel"
    assert trips[0].total_diet_pln == Decimal("4915.98")
    assert trips[0].date_to.isoformat() == "2026-03-25"
    assert trips[0].test is False


def test_export_delegations_csv_writes_public_format(tmp_path):
    source = tmp_path / "source.csv"
    source.write_text(
        "date_to;amount_pln;description\n" "2026-03-25;4915.98;Delegacja\n",
        encoding="utf-8",
    )
    out_file = tmp_path / "out.csv"

    export_delegations_csv(load_delegations_csv(source), out_file)
    content = out_file.read_text(encoding="utf-8-sig")

    assert "number;date_from;date_to;year;city;description" in content
    assert "4915.98" in content
