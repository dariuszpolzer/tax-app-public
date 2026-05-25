from dataclasses import dataclass, field
from decimal import Decimal
from enum import Enum


class TaxationForm(str, Enum):
    SCALE = "scale"
    LINEAR = "linear"
    LUMP_SUM = "lump_sum"


@dataclass(frozen=True)
class BusinessProfile:
    enabled: bool = True
    taxation_form: TaxationForm = TaxationForm.SCALE
    vat_payer: bool = True


@dataclass(frozen=True)
class PensionProfile:
    enabled: bool = False
    annual_income: Decimal = Decimal("0.00")


@dataclass(frozen=True)
class SpouseProfile:
    enabled: bool = False
    annual_income: Decimal = Decimal("0.00")


@dataclass(frozen=True)
class TaxpayerProfile:
    is_pensioner: bool = False
    settle_jointly_with_spouse: bool = False
    business: BusinessProfile = field(default_factory=BusinessProfile)
    pension: PensionProfile = field(default_factory=PensionProfile)
    spouse: SpouseProfile = field(default_factory=SpouseProfile)


@dataclass(frozen=True)
class TaxScenario:
    year: int
    taxpayer: TaxpayerProfile = field(default_factory=TaxpayerProfile)
