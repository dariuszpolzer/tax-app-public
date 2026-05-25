import json
from decimal import Decimal

import pytest

from config_loader import load_config, load_tax_scenario_from_config
from tax_profile import TaxationForm


def test_load_config_valid_with_delegations_csv(tmp_path):
    delegations_csv = tmp_path / "delegations.csv"
    delegations_csv.write_text("date_to;amount_pln\n2026-01-31;100.00\n", encoding="utf-8")

    jpk_folder = tmp_path / "jpk"
    jpk_folder.mkdir()

    config_path = tmp_path / "config.json"
    config_path.write_text(
        json.dumps(
            {
                "delegations_csv": str(delegations_csv),
                "jpk_folder": str(jpk_folder),
            }
        ),
        encoding="utf-8",
    )

    config = load_config(config_path)

    assert config["delegations_csv"] == str(delegations_csv)
    assert config["jpk_folder"] == str(jpk_folder)


def test_load_config_missing_file():
    with pytest.raises(FileNotFoundError):
        load_config("missing-config.json")


def test_load_config_can_skip_jpk_folder_validation(tmp_path):
    config_path = tmp_path / "config.json"
    config_path.write_text(
        json.dumps(
            {
                "jpk_folder": "unused",
            }
        ),
        encoding="utf-8",
    )

    config = load_config(config_path, require_jpk=False)

    assert config["jpk_folder"] == "unused"


def test_load_config_accepts_legacy_trips_xml(tmp_path):
    trips_xml = tmp_path / "trips.xml"
    trips_xml.write_text("<Voyages></Voyages>", encoding="utf-8")
    jpk_folder = tmp_path / "jpk"
    jpk_folder.mkdir()

    config_path = tmp_path / "config.json"
    config_path.write_text(
        json.dumps(
            {
                "trips_xml": str(trips_xml),
                "jpk_folder": str(jpk_folder),
            }
        ),
        encoding="utf-8",
    )

    config = load_config(config_path)

    assert config["trips_xml"] == str(trips_xml)


def test_load_tax_scenario_uses_defaults_for_legacy_config():
    scenario = load_tax_scenario_from_config({}, 2026)

    assert scenario.year == 2026
    assert scenario.taxpayer.is_pensioner is False
    assert scenario.taxpayer.settle_jointly_with_spouse is False
    assert scenario.taxpayer.business.enabled is True
    assert scenario.taxpayer.business.taxation_form == TaxationForm.SCALE
    assert scenario.taxpayer.business.vat_payer is True
    assert scenario.taxpayer.pension.enabled is False
    assert scenario.taxpayer.pension.annual_income == Decimal("0.00")
    assert scenario.taxpayer.spouse.enabled is False
    assert scenario.taxpayer.spouse.annual_income == Decimal("0.00")


def test_load_tax_scenario_reads_pensioner_joint_settlement_profile():
    scenario = load_tax_scenario_from_config(
        {
            "taxpayer": {
                "is_pensioner": True,
                "settle_jointly_with_spouse": True,
            },
            "business": {
                "enabled": True,
                "taxation_form": "scale",
                "vat_payer": True,
            },
            "pension": {
                "enabled": True,
                "annual_income": "42000.50",
            },
            "spouse": {
                "enabled": True,
                "annual_income": "18000.25",
            },
        },
        2026,
    )

    assert scenario.taxpayer.is_pensioner is True
    assert scenario.taxpayer.settle_jointly_with_spouse is True
    assert scenario.taxpayer.business.taxation_form == TaxationForm.SCALE
    assert scenario.taxpayer.pension.enabled is True
    assert scenario.taxpayer.pension.annual_income == Decimal("42000.50")
    assert scenario.taxpayer.spouse.enabled is True
    assert scenario.taxpayer.spouse.annual_income == Decimal("18000.25")
