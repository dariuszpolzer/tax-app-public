import json
from decimal import Decimal
from pathlib import Path

from tax_profile import (
    BusinessProfile,
    PensionProfile,
    SpouseProfile,
    TaxationForm,
    TaxpayerProfile,
    TaxScenario,
)


def load_config(path="config.json", require_jpk=True):
    config_path = Path(path)

    if not config_path.exists():
        raise FileNotFoundError(f"Brak pliku konfiguracji: {config_path}")

    with open(config_path, encoding="utf-8") as f:
        config = json.load(f)

    if "jpk_folder" not in config:
        raise KeyError("Brak wymaganego klucza w config.json: jpk_folder")

    jpk_folder = Path(config["jpk_folder"])

    delegations_csv = config.get("delegations_csv")
    trips_xml = config.get("trips_xml")

    if delegations_csv and not Path(delegations_csv).exists():
        raise FileNotFoundError(f"Nie istnieje plik delegacji CSV: {delegations_csv}")

    if trips_xml and not Path(trips_xml).exists():
        raise FileNotFoundError(f"Nie istnieje plik delegacji XML: {trips_xml}")

    if require_jpk and not jpk_folder.exists():
        raise FileNotFoundError(f"Nie istnieje folder JPK: {jpk_folder}")

    return config


def decimal_from_config(value) -> Decimal:
    return Decimal(str(value or "0.00"))


def load_tax_scenario_from_config(config, year: int) -> TaxScenario:
    taxpayer_config = config.get("taxpayer", {})
    business_config = config.get("business", {})
    pension_config = config.get("pension", {})
    spouse_config = config.get("spouse", {})

    taxation_form = TaxationForm(business_config.get("taxation_form", TaxationForm.SCALE))

    return TaxScenario(
        year=year,
        taxpayer=TaxpayerProfile(
            is_pensioner=bool(taxpayer_config.get("is_pensioner", False)),
            settle_jointly_with_spouse=bool(
                taxpayer_config.get("settle_jointly_with_spouse", False)
            ),
            business=BusinessProfile(
                enabled=bool(business_config.get("enabled", True)),
                taxation_form=taxation_form,
                vat_payer=bool(business_config.get("vat_payer", True)),
            ),
            pension=PensionProfile(
                enabled=bool(pension_config.get("enabled", False)),
                annual_income=decimal_from_config(pension_config.get("annual_income", "0.00")),
            ),
            spouse=SpouseProfile(
                enabled=bool(spouse_config.get("enabled", False)),
                annual_income=decimal_from_config(spouse_config.get("annual_income", "0.00")),
            ),
        ),
    )
