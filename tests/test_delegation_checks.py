from decimal import Decimal
from pathlib import Path

from delegation_checks import build_delegation_check_report
from parser_trips import load_voyages


def test_build_delegation_check_report_for_vba_reference():
    trips = load_voyages(Path("tests/data/vba_delegations_2026.xml"))

    report = build_delegation_check_report(trips)

    assert report.trip_count == 6
    assert report.total_pln == Decimal("21053.51")
    assert report.monthly_totals == {
        "2026-01": Decimal("6055.63"),
        "2026-02": Decimal("4102.86"),
        "2026-03": Decimal("4915.98"),
        "2026-04": Decimal("3825.91"),
        "2026-05": Decimal("2153.13"),
    }
    assert report.test_trip_numbers == ["T002/2026", "T003/2026", "T004/2026", "T006/2026"]
    assert any("T001/2026" in warning and "poza zakresem" in warning for warning in report.warnings)
    assert any("T003/2026" in warning and "biale znaki" in warning for warning in report.warnings)


def test_check_delegations_cli_outputs_report(capsys, monkeypatch, tmp_path):
    config_path = tmp_path / "config.json"
    trips_path = Path("tests/data/vba_delegations_2026.xml").resolve()
    config_path.write_text(
        f'{{"trips_xml": "{trips_path.as_posix()}", "jpk_folder": "unused"}}',
        encoding="utf-8",
    )

    monkeypatch.setattr(
        "sys.argv",
        ["tax-app", "--config", str(config_path), "--year", "2026", "--check-delegations"],
    )

    from main import main

    main()

    output = capsys.readouterr().out

    assert "KONTROLA DELEGACJI" in output
    assert "Liczba delegacji: 6" in output
    assert "Suma diet: 21053.51 PLN" in output
    assert "2026-02: 4102.86 PLN" in output
    assert "Delegacje Test=true" in output
