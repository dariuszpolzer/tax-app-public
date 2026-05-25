from decimal import Decimal

import pytest

from health_contribution import (
    calculate_health_contribution_monthly,
    calculate_health_contribution_scale,
)


def test_health_contribution_uses_january_2026_minimum_when_income_is_low():
    result = calculate_health_contribution_scale(
        month="2026-01",
        revenue=Decimal("1000.00"),
        purchase_costs=Decimal("1000.00"),
    )

    assert result.business_income == Decimal("0.00")
    assert result.minimum_contribution == Decimal("314.96")
    assert result.contribution == Decimal("314.96")


def test_health_contribution_uses_nine_percent_when_income_exceeds_minimum():
    result = calculate_health_contribution_scale(
        month="2026-02",
        revenue=Decimal("10000.00"),
        purchase_costs=Decimal("1000.00"),
    )

    assert result.business_income == Decimal("9000.00")
    assert result.minimum_contribution == Decimal("324.41")
    assert result.contribution == Decimal("810.00")


def test_health_contribution_monthly_sums_contributions():
    summary = calculate_health_contribution_monthly(
        monthly_jpk={
            "2026-01": {
                "sales_net": Decimal("1000.00"),
                "purchase_net": Decimal("1000.00"),
            },
            "2026-02": {
                "sales_net": Decimal("10000.00"),
                "purchase_net": Decimal("1000.00"),
            },
        },
        delegations_monthly={},
        other_costs_monthly={},
    )

    assert summary.monthly["2026-01"].contribution == Decimal("314.96")
    assert summary.monthly["2026-02"].contribution == Decimal("810.00")
    assert summary.total == Decimal("1124.96")


def test_health_contribution_rejects_year_without_rules():
    with pytest.raises(NotImplementedError):
        calculate_health_contribution_scale(
            month="2027-01",
            revenue=Decimal("1000.00"),
        )
