from decimal import Decimal

import pytest

from calculator_tax import calculate_pit_scale
from settlement import BusinessIncome, calculate_annual_settlement
from tax_profile import (
    BusinessProfile,
    PensionProfile,
    SpouseProfile,
    TaxationForm,
    TaxpayerProfile,
    TaxScenario,
)


def test_annual_settlement_matches_scale_pit_for_business_income():
    scenario = TaxScenario(year=2026)
    business_income = BusinessIncome(
        revenue=Decimal("100000.00"),
        purchase_costs=Decimal("20000.00"),
        delegation_costs=Decimal("5000.00"),
        other_costs=Decimal("1000.00"),
    )

    settlement = calculate_annual_settlement(scenario, business_income)
    expected = calculate_pit_scale(
        income=Decimal("100000.00"),
        other_costs=Decimal("21000.00"),
        delegation_costs=Decimal("5000.00"),
    )

    assert settlement.pit == expected


def test_annual_settlement_adds_pension_income_to_scale_pit():
    scenario = TaxScenario(
        year=2026,
        taxpayer=TaxpayerProfile(
            is_pensioner=True,
            pension=PensionProfile(
                enabled=True,
                annual_income=Decimal("42000.00"),
            ),
        ),
    )
    business_income = BusinessIncome(
        revenue=Decimal("100000.00"),
        purchase_costs=Decimal("20000.00"),
        delegation_costs=Decimal("5000.00"),
        other_costs=Decimal("1000.00"),
    )

    settlement = calculate_annual_settlement(scenario, business_income)
    expected = calculate_pit_scale(
        income=Decimal("142000.00"),
        other_costs=Decimal("21000.00"),
        delegation_costs=Decimal("5000.00"),
    )

    assert settlement.pension_income == Decimal("42000.00")
    assert settlement.spouse_income == Decimal("0.00")
    assert settlement.individual_pit == expected
    assert settlement.joint_pit is None
    assert settlement.joint_tax_saving == Decimal("0.00")
    assert settlement.pit == expected


def test_annual_settlement_rejects_unsupported_taxation_form():
    scenario = TaxScenario(
        year=2026,
        taxpayer=TaxpayerProfile(business=BusinessProfile(taxation_form=TaxationForm.LINEAR)),
    )

    with pytest.raises(NotImplementedError):
        calculate_annual_settlement(
            scenario,
            BusinessIncome(revenue=Decimal("100000.00")),
        )


def test_annual_settlement_calculates_joint_settlement_from_half_combined_income():
    scenario = TaxScenario(
        year=2026,
        taxpayer=TaxpayerProfile(
            is_pensioner=True,
            settle_jointly_with_spouse=True,
            pension=PensionProfile(
                enabled=True,
                annual_income=Decimal("42000.00"),
            ),
            spouse=SpouseProfile(
                enabled=True,
                annual_income=Decimal("18000.00"),
            ),
        ),
    )
    business_income = BusinessIncome(
        revenue=Decimal("100000.00"),
        purchase_costs=Decimal("20000.00"),
        delegation_costs=Decimal("5000.00"),
        other_costs=Decimal("1000.00"),
    )

    settlement = calculate_annual_settlement(scenario, business_income)

    # Total taxable income: 100000 + 42000 + 18000 - 20000 - 1000 - 5000 = 134000.
    expected_half = calculate_pit_scale(income=Decimal("67000.00"))
    expected_individual_taxpayer = calculate_pit_scale(
        income=Decimal("142000.00"),
        other_costs=Decimal("21000.00"),
        delegation_costs=Decimal("5000.00"),
    )
    expected_individual_spouse = calculate_pit_scale(income=Decimal("18000.00"))

    assert settlement.pension_income == Decimal("42000.00")
    assert settlement.spouse_income == Decimal("18000.00")
    assert settlement.pit.income == Decimal("160000.00")
    assert settlement.pit.taxable_income == Decimal("134000.00")
    assert settlement.pit.tax == expected_half.tax * Decimal("2")
    assert settlement.individual_pit.tax == (
        expected_individual_taxpayer.tax + expected_individual_spouse.tax
    )
    assert settlement.joint_pit is not None
    assert settlement.joint_pit.tax == settlement.pit.tax
    assert settlement.joint_tax_saving == Decimal("1440.00")
