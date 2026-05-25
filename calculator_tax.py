from dataclasses import dataclass
from decimal import ROUND_HALF_UP, Decimal

MONEY = Decimal("0.01")


def to_decimal(value) -> Decimal:
    return Decimal(str(value))


def money(value: Decimal) -> Decimal:
    return value.quantize(MONEY, rounding=ROUND_HALF_UP)


@dataclass
class TaxResult:
    income: Decimal
    delegation_costs: Decimal
    taxable_income: Decimal
    tax: Decimal


def calculate_pit_scale(
    income,
    delegation_costs=Decimal("0.00"),
    other_costs=Decimal("0.00"),
) -> TaxResult:
    income = to_decimal(income)
    delegation_costs = to_decimal(delegation_costs)
    other_costs = to_decimal(other_costs)

    taxable_income = max(
        Decimal("0.00"),
        income - delegation_costs - other_costs,
    )

    if taxable_income <= Decimal("30000"):
        tax = Decimal("0.00")
    elif taxable_income <= Decimal("120000"):
        tax = taxable_income * Decimal("0.12") - Decimal("3600")
    else:
        tax = Decimal("10800") + (taxable_income - Decimal("120000")) * Decimal("0.32")

    return TaxResult(
        income=money(income),
        delegation_costs=money(delegation_costs),
        taxable_income=money(taxable_income),
        tax=money(tax),
    )


def calculate_tax(income, costs, delegation_costs) -> Decimal:
    return calculate_pit_scale(
        income=income,
        other_costs=costs,
        delegation_costs=delegation_costs,
    ).tax
