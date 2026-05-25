from dataclasses import dataclass
from decimal import Decimal

from calculator_tax import TaxResult, calculate_pit_scale, money
from tax_profile import TaxationForm, TaxScenario

ZERO = Decimal("0.00")


@dataclass(frozen=True)
class BusinessIncome:
    revenue: Decimal
    purchase_costs: Decimal = ZERO
    delegation_costs: Decimal = ZERO
    other_costs: Decimal = ZERO

    @property
    def total_costs(self) -> Decimal:
        return self.purchase_costs + self.delegation_costs + self.other_costs


@dataclass(frozen=True)
class AnnualSettlement:
    scenario: TaxScenario
    business_income: BusinessIncome
    pension_income: Decimal
    spouse_income: Decimal
    individual_pit: TaxResult
    joint_pit: TaxResult | None
    joint_tax_saving: Decimal
    pit: TaxResult


def calculate_joint_pit_scale(
    total_income: Decimal,
    other_costs: Decimal = ZERO,
    delegation_costs: Decimal = ZERO,
) -> TaxResult:
    taxable_income = max(
        ZERO,
        total_income - other_costs - delegation_costs,
    )
    half_result = calculate_pit_scale(income=taxable_income / Decimal("2"))

    return TaxResult(
        income=money(total_income),
        delegation_costs=money(delegation_costs),
        taxable_income=money(taxable_income),
        tax=money(half_result.tax * Decimal("2")),
    )


def calculate_annual_settlement(
    scenario: TaxScenario,
    business_income: BusinessIncome,
) -> AnnualSettlement:
    taxation_form = scenario.taxpayer.business.taxation_form
    taxpayer = scenario.taxpayer

    if taxation_form != TaxationForm.SCALE:
        raise NotImplementedError(
            f"Forma opodatkowania nie jest jeszcze obsługiwana: {taxation_form.value}"
        )

    pension_income = ZERO
    if taxpayer.pension.enabled:
        pension_income = taxpayer.pension.annual_income

    spouse_income = ZERO
    if taxpayer.spouse.enabled:
        spouse_income = taxpayer.spouse.annual_income

    taxpayer_income = business_income.revenue + pension_income
    total_income = taxpayer_income + spouse_income
    total_other_costs = business_income.purchase_costs + business_income.other_costs

    taxpayer_pit = calculate_pit_scale(
        income=taxpayer_income,
        other_costs=total_other_costs,
        delegation_costs=business_income.delegation_costs,
    )
    spouse_pit = calculate_pit_scale(income=spouse_income)
    individual_pit = TaxResult(
        income=money(taxpayer_income + spouse_income),
        delegation_costs=money(business_income.delegation_costs),
        taxable_income=money(taxpayer_pit.taxable_income + spouse_pit.taxable_income),
        tax=money(taxpayer_pit.tax + spouse_pit.tax),
    )

    joint_pit = None
    if taxpayer.spouse.enabled or taxpayer.settle_jointly_with_spouse:
        joint_pit = calculate_joint_pit_scale(
            total_income=total_income,
            other_costs=total_other_costs,
            delegation_costs=business_income.delegation_costs,
        )

    if taxpayer.settle_jointly_with_spouse:
        pit = joint_pit
    else:
        pit = individual_pit

    joint_tax_saving = ZERO
    if joint_pit is not None:
        joint_tax_saving = money(individual_pit.tax - joint_pit.tax)

    return AnnualSettlement(
        scenario=scenario,
        business_income=business_income,
        pension_income=pension_income,
        spouse_income=spouse_income,
        individual_pit=individual_pit,
        joint_pit=joint_pit,
        joint_tax_saving=joint_tax_saving,
        pit=pit,
    )
