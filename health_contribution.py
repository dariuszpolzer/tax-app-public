from dataclasses import dataclass
from decimal import Decimal

from calculator_tax import money

ZERO = Decimal("0.00")


@dataclass(frozen=True)
class HealthContributionRules:
    rate: Decimal
    minimum_by_month: dict[int, Decimal]

    def minimum_for_month(self, month: int) -> Decimal:
        return self.minimum_by_month.get(month, self.minimum_by_month[0])


@dataclass(frozen=True)
class HealthContributionMonth:
    month: str
    business_income: Decimal
    minimum_contribution: Decimal
    contribution: Decimal


@dataclass(frozen=True)
class HealthContributionSummary:
    monthly: dict[str, HealthContributionMonth]
    total: Decimal


HEALTH_RULES_BY_YEAR = {
    2026: HealthContributionRules(
        rate=Decimal("0.09"),
        minimum_by_month={
            0: Decimal("324.41"),
            1: Decimal("314.96"),
        },
    )
}


def get_health_contribution_rules(year: int) -> HealthContributionRules:
    try:
        return HEALTH_RULES_BY_YEAR[year]
    except KeyError as error:
        raise NotImplementedError(f"Brak reguł składki zdrowotnej dla roku: {year}") from error


def calculate_health_contribution_scale(
    month: str,
    revenue: Decimal,
    purchase_costs: Decimal = ZERO,
    delegation_costs: Decimal = ZERO,
    other_costs: Decimal = ZERO,
) -> HealthContributionMonth:
    year = int(month[:4])
    month_number = int(month[5:7])
    rules = get_health_contribution_rules(year)

    business_income = max(
        ZERO,
        revenue - purchase_costs - delegation_costs - other_costs,
    )
    minimum = rules.minimum_for_month(month_number)
    contribution = max(money(business_income * rules.rate), minimum)

    return HealthContributionMonth(
        month=month,
        business_income=money(business_income),
        minimum_contribution=money(minimum),
        contribution=money(contribution),
    )


def calculate_health_contribution_monthly(
    monthly_jpk,
    delegations_monthly,
    other_costs_monthly,
) -> HealthContributionSummary:
    monthly = {}
    total = ZERO

    months = sorted(
        set(monthly_jpk.keys()) | set(delegations_monthly.keys()) | set(other_costs_monthly.keys())
    )

    for month in months:
        data = monthly_jpk.get(month, {})
        result = calculate_health_contribution_scale(
            month=month,
            revenue=Decimal(str(data.get("sales_net", ZERO))),
            purchase_costs=Decimal(str(data.get("purchase_net", ZERO))),
            delegation_costs=Decimal(str(delegations_monthly.get(month, ZERO))),
            other_costs=Decimal(str(other_costs_monthly.get(month, ZERO))),
        )
        monthly[month] = result
        total += result.contribution

    return HealthContributionSummary(monthly=monthly, total=money(total))
