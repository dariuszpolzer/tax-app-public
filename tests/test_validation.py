import json
import shutil
from pathlib import Path

from validation import validate_config_data


def write_config(tmp_path, delegations_csv, jpk_dir, other_costs_csv):
    config_path = tmp_path / "config.json"
    config_path.write_text(
        json.dumps(
            {
                "delegations_csv": str(delegations_csv),
                "jpk_folder": str(jpk_dir),
                "other_costs_csv": str(other_costs_csv),
            }
        ),
        encoding="utf-8",
    )
    return config_path


def test_validate_config_data_reports_valid_inputs(tmp_path):
    repo_root = Path(__file__).resolve().parents[1]
    jpk_dir = tmp_path / "jpk"
    jpk_dir.mkdir()
    shutil.copyfile(
        repo_root / "tests" / "data" / "example_jpk.xml",
        jpk_dir / "JPK_FA_03_2026.xml",
    )

    delegations_csv = tmp_path / "delegations.csv"
    delegations_csv.write_text("date_to;amount_pln\n2026-03-20;123,45\n", encoding="utf-8")
    other_costs_csv = tmp_path / "other_costs.csv"
    other_costs_csv.write_text(
        "date;type;description;amount_pln\n2026-03-18;office;Koszt;50,00\n",
        encoding="utf-8",
    )

    report = validate_config_data(
        write_config(tmp_path, delegations_csv, jpk_dir, other_costs_csv),
        2026,
    )

    assert report.ok
    assert any("JPK: 1 plików XML" in item for item in report.info)


def test_validate_config_data_reports_bad_delegations_csv(tmp_path):
    jpk_dir = tmp_path / "jpk"
    jpk_dir.mkdir()
    delegations_csv = tmp_path / "delegations.csv"
    delegations_csv.write_text("date_to;amount_pln\nbad-date;abc\n", encoding="utf-8")

    report = validate_config_data(
        write_config(tmp_path, delegations_csv, jpk_dir, tmp_path / "missing_other_costs.csv"),
        2026,
        require_jpk=False,
    )

    assert not report.ok
    assert any("Nieprawidłowa data" in error for error in report.errors)
    assert any("Nieprawidłowa kwota" in error for error in report.errors)
