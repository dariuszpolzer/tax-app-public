from dataclasses import dataclass
from decimal import Decimal

from calculator_costs import sum_trip_costs, sum_trip_costs_by_month


@dataclass(frozen=True)
class DelegationCheckReport:
    trip_count: int
    total_pln: Decimal
    monthly_totals: dict[str, Decimal]
    test_trip_numbers: list[str]
    warnings: list[str]


def build_delegation_check_report(trips) -> DelegationCheckReport:
    warnings = []

    for trip in trips:
        if trip.date_from and trip.date_to and trip.date_from > trip.date_to:
            warnings.append(
                f"{trip.nr_del}: data Od {trip.date_from} jest pozniejsza niz Do {trip.date_to}"
            )

        for item in trip.iters:
            for label, value in (
                ("Wyjazd", item.depart_at),
                ("Granica", item.border_at),
                ("Przyjazd", item.arrive_at),
            ):
                if not value or not trip.date_from or not trip.date_to:
                    continue
                item_date = value.date()
                if item_date < trip.date_from or item_date > trip.date_to:
                    warnings.append(
                        f"{trip.nr_del}: {label} {item_date} poza zakresem "
                        f"{trip.date_from} - {trip.date_to}"
                    )

        for diet in trip.diets:
            expected = (diet.amount * diet.fx_rate).quantize(Decimal("0.01"))
            if abs(expected - diet.amount_pln) > Decimal("0.02"):
                warnings.append(
                    f"{trip.nr_del}: dieta {diet.nr} ma {diet.amount_pln} PLN, "
                    f"a kwota*dietowy kurs daje {expected} PLN"
                )

            if diet.fx_table:
                table = diet.fx_table.strip()
                if table != diet.fx_table:
                    warnings.append(f"{trip.nr_del}: tabela kursu zawiera biale znaki")

    return DelegationCheckReport(
        trip_count=len(trips),
        total_pln=sum_trip_costs(trips),
        monthly_totals=dict(sorted(sum_trip_costs_by_month(trips).items())),
        test_trip_numbers=[trip.nr_del for trip in trips if trip.test],
        warnings=warnings,
    )
