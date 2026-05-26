import json
import shutil
import subprocess
import sys
from pathlib import Path


def test_cli_generates_reports_from_config_with_delegations_csv(tmp_path):
    repo_root = Path(__file__).resolve().parents[1]

    jpk_dir = tmp_path / "jpk"
    jpk_dir.mkdir()
    shutil.copyfile(
        repo_root / "tests" / "data" / "example_jpk.xml",
        jpk_dir / "JPK_FA_03_2026.xml",
    )

    delegations_csv = tmp_path / "delegations.csv"
    delegations_csv.write_text(
        "number;date_from;date_to;year;city;description;transport;employee;amount_pln;test\n"
        "DEL/1/2026;2026-03-01;2026-03-20;2026;Berlin;Delegacja;auto;Jan Testowy;123,45;false\n",
        encoding="utf-8",
    )

    other_costs_csv = tmp_path / "other_costs.csv"
    other_costs_csv.write_text(
        "date;type;description;amount_pln\n" "2026-03-18;office;Testowy koszt;50,00\n",
        encoding="utf-8",
    )

    config_path = tmp_path / "config.json"
    config_path.write_text(
        json.dumps(
            {
                "taxpayer": {
                    "is_pensioner": False,
                    "settle_jointly_with_spouse": False,
                },
                "business": {
                    "enabled": True,
                    "taxation_form": "scale",
                    "vat_payer": True,
                },
                "health_contribution": {
                    "income_basis": "previous_month",
                },
                "delegations_csv": str(delegations_csv),
                "jpk_folder": str(jpk_dir),
                "other_costs_csv": str(other_costs_csv),
            }
        ),
        encoding="utf-8",
    )

    out_dir = tmp_path / "reports"

    result = subprocess.run(
        [
            sys.executable,
            "main.py",
            "--year",
            "2026",
            "--config",
            str(config_path),
            "--out-dir",
            str(out_dir),
        ],
        cwd=repo_root,
        text=True,
        encoding="utf-8",
        errors="replace",
        capture_output=True,
        check=False,
    )

    assert result.returncode == 0, result.stdout + result.stderr
    assert "=== TAX APP OK ===" in result.stdout
    assert "RAPORT SKŁADKI ZDROWOTNEJ JDG" in result.stdout

    monthly_report = out_dir / "report_monthly.csv"
    yearly_report = out_dir / "report_yearly.csv"
    excel_report = out_dir / "report_tax.xlsx"

    assert monthly_report.exists()
    assert yearly_report.exists()
    assert excel_report.exists()
    assert excel_report.stat().st_size > 0

    monthly_content = monthly_report.read_text(encoding="utf-8-sig")
    assert "2026-03;1000,00;200,00;230,00;46,00;184,00;123,45;50,00" in monthly_content
    assert "Dochód JDG do zdrowotnej" in monthly_content
    assert "Składka zdrowotna JDG" in monthly_content

    yearly_content = yearly_report.read_text(encoding="utf-8-sig")
    assert "Delegacje;1" in yearly_content
    assert "Koszty delegacji;123,45" in yearly_content
    assert "Inne koszty;50,00" in yearly_content
    assert "Składka zdrowotna JDG" in yearly_content
