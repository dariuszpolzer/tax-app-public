import argparse
import sys
from datetime import datetime
from decimal import Decimal
from pathlib import Path

from calculator_costs import sum_trip_costs, sum_trip_costs_by_month
from calculator_tax import calculate_pit_scale
from config_loader import load_config, load_tax_scenario_from_config
from delegation_checks import build_delegation_check_report
from delegations_csv import load_delegations_csv
from health_contribution import PREVIOUS_MONTH, calculate_health_contribution_monthly
from jpk.calculator_jpk import sum_jpk_folder
from other_costs import load_other_costs, sum_other_costs_by_month
from parser_trips import load_voyages
from report.export_excel import export_excel_report
from report.export_reports import export_monthly_report, export_yearly_report
from settlement import BusinessIncome, calculate_annual_settlement

ZERO = Decimal("0.00")


def parse_args():
    parser = argparse.ArgumentParser(description="Tax App - lokalne raporty podatkowe")
    parser.add_argument("--year", type=int, help="Rok raportu, np. 2026")
    parser.add_argument(
        "--month",
        type=int,
        default=0,
        help="Miesiąc raportu 1-12. Brak lub 0 oznacza cały rok.",
    )
    parser.add_argument("--config", default="config.json", help="Ścieżka do pliku config.json")
    parser.add_argument("--out-dir", default=".", help="Katalog wyjściowy raportów")
    parser.add_argument(
        "--check-delegations",
        action="store_true",
        help="Sprawdza tylko delegacje z trips_xml i wypisuje sumy oraz ostrzeżenia",
    )

    args = parser.parse_args()

    if args.month < 0 or args.month > 12:
        raise ValueError(f"Nieprawidłowy miesiąc: {args.month}")

    return args


def month_is_in_scope(month: str, year: int, until_month: int = 0) -> bool:
    if month == "unknown" or not month.startswith(str(year)):
        return False

    if until_month == 0:
        return True

    return int(month[5:7]) <= until_month


def trip_is_in_scope(trip, year: int, until_month: int = 0) -> bool:
    if trip.year != year:
        return False

    if until_month == 0:
        return True

    if not trip.date_to:
        return False

    return trip.date_to.month <= until_month


def filter_monthly(monthly_all, year: int, until_month: int = 0):
    return {
        month: data
        for month, data in monthly_all.items()
        if month_is_in_scope(month, year, until_month)
    }


def filter_decimal_monthly(monthly_all, year: int, until_month: int = 0):
    return {
        month: value
        for month, value in monthly_all.items()
        if month_is_in_scope(month, year, until_month)
    }


def build_yearly_summary(monthly):
    yearly = {
        "sales_net": ZERO,
        "sales_vat": ZERO,
        "purchase_net": ZERO,
        "purchase_vat": ZERO,
    }

    for data in monthly.values():
        yearly["sales_net"] += data["sales_net"]
        yearly["sales_vat"] += data["sales_vat"]
        yearly["purchase_net"] += data["purchase_net"]
        yearly["purchase_vat"] += data["purchase_vat"]

    yearly["vat_to_pay"] = yearly["sales_vat"] - yearly["purchase_vat"]

    return yearly


def build_pit_monthly(monthly, delegations_monthly, other_costs_monthly):
    pit_monthly = {}

    paid_pit = ZERO
    income_ytd = ZERO
    costs_ytd = ZERO
    delegations_ytd = ZERO
    other_costs_ytd = ZERO

    months = sorted(
        set(monthly.keys()) | set(delegations_monthly.keys()) | set(other_costs_monthly.keys())
    )

    for month in months:
        data = monthly.get(
            month,
            {
                "sales_net": ZERO,
                "purchase_net": ZERO,
            },
        )

        income_ytd += Decimal(str(data.get("sales_net", ZERO)))
        costs_ytd += Decimal(str(data.get("purchase_net", ZERO)))
        delegations_ytd += Decimal(str(delegations_monthly.get(month, ZERO)))
        other_costs_ytd += Decimal(str(other_costs_monthly.get(month, ZERO)))

        taxable_income_ytd = max(
            ZERO,
            income_ytd - costs_ytd - delegations_ytd - other_costs_ytd,
        )

        pit_ytd = calculate_pit_scale(
            income=income_ytd,
            other_costs=costs_ytd + other_costs_ytd,
            delegation_costs=delegations_ytd,
        ).tax

        pit_for_month = max(ZERO, pit_ytd - paid_pit)
        paid_pit += pit_for_month

        pit_monthly[month] = {
            "delegations_cumulative": delegations_ytd,
            "other_costs_cumulative": other_costs_ytd,
            "income_cumulative": taxable_income_ytd,
            "pit_cumulative": pit_ytd,
            "pit_payment": pit_for_month,
        }

    return pit_monthly


def print_delegation_check_report(trips):
    report = build_delegation_check_report(trips)

    print("\nKONTROLA DELEGACJI")
    print(f"Liczba delegacji: {report.trip_count}")
    print(f"Suma diet: {report.total_pln:.2f} PLN")

    print("\nMiesięcznie:")
    for month, total in report.monthly_totals.items():
        print(f"{month}: {total:.2f} PLN")

    if report.test_trip_numbers:
        print("\nDelegacje Test=true:")
        for number in report.test_trip_numbers:
            print(f"- {number}")

    if report.warnings:
        print("\nOstrzeżenia:")
        for warning in report.warnings:
            print(f"WARN {warning}")
    else:
        print("\nOstrzeżenia: brak")


def print_delegations(trips):
    print("\nRAPORT DELEGACJI SZCZEGÓŁOWY")

    for trip in trips:
        print(f"\n{trip.nr_del}  suma: {trip.total_diet_pln:.2f} PLN")

        for diet in trip.diets:
            print(
                f"  {diet.country} | "
                f"{diet.units} x {diet.rate} {diet.currency} | "
                f"{diet.amount_pln:.2f} PLN"
            )


def print_monthly_jpk(monthly):
    print("\nRAPORT MIESIĘCZNY JPK")

    for month, data in sorted(monthly.items()):
        vat_to_pay = data["sales_vat"] - data["purchase_vat"]

        print(
            f"{month} | "
            f"sprzedaż: {data['sales_net']:.2f} PLN | "
            f"koszty: {data['purchase_net']:.2f} PLN | "
            f"VAT należny: {data['sales_vat']:.2f} PLN | "
            f"VAT naliczony: {data['purchase_vat']:.2f} PLN | "
            f"VAT: {vat_to_pay:.2f} PLN"
        )


def print_corrections(monthly):
    print("\nRAPORT KOREKT")

    for month, data in sorted(monthly.items()):
        sales_corr = data["sales_corrections_net"]
        purchase_corr = data["purchase_corrections_net"]

        if sales_corr != 0 or purchase_corr != 0:
            print(
                f"{month} | "
                f"korekty sprzedaży netto: {sales_corr:.2f} PLN | "
                f"korekty zakupów netto: {purchase_corr:.2f} PLN"
            )


def print_pit_monthly(pit_monthly):
    print("\nRAPORT PIT JDG MIESIĘCZNIE / NARASTAJĄCO")

    for month, data in sorted(pit_monthly.items()):
        print(
            f"{month} | "
            f"delegacje narastająco: {data['delegations_cumulative']:.2f} PLN | "
            f"inne koszty narastająco: {data['other_costs_cumulative']:.2f} PLN | "
            f"dochód JDG narastająco: {data['income_cumulative']:.2f} PLN | "
            f"PIT JDG narastająco: {data['pit_cumulative']:.2f} PLN | "
            f"zaliczka PIT JDG: {data['pit_payment']:.2f} PLN"
        )


def print_health_monthly(health_monthly):
    print("\nRAPORT SKŁADKI ZDROWOTNEJ JDG")

    for month, data in sorted(health_monthly.items()):
        print(
            f"{month} | "
            f"dochód JDG: {data.business_income:.2f} PLN | "
            f"minimum: {data.minimum_contribution:.2f} PLN | "
            f"składka zdrowotna: {data.contribution:.2f} PLN"
        )


def print_yearly_summary(
    year,
    trips,
    delegation_costs,
    other_costs_total,
    pension_income,
    spouse_income,
    individual_pit,
    joint_pit,
    joint_tax_saving,
    health_contribution_total,
    yearly,
    pit_result,
):
    print("\nRAPORT ROCZNY")
    print(f"Rok: {year}")
    print(f"Liczba delegacji: {len(trips)}")
    print(f"Koszty delegacji: {delegation_costs:.2f} PLN")
    print(f"Inne koszty: {other_costs_total:.2f} PLN")
    print(f"Emerytura: {pension_income:.2f} PLN")
    print(f"Dochód małżonka: {spouse_income:.2f} PLN")
    print(f"Sprzedaż netto JPK: {yearly['sales_net']:.2f} PLN")
    print(f"Koszty netto JPK: {yearly['purchase_net']:.2f} PLN")
    print(f"Podstawa PIT: {pit_result.taxable_income:.2f} PLN")
    print(f"PIT: {pit_result.tax:.2f} PLN")
    print(f"Składka zdrowotna JDG: {health_contribution_total:.2f} PLN")
    print(f"PIT osobno: {individual_pit.tax:.2f} PLN")
    if joint_pit is not None:
        print(f"PIT wspólnie: {joint_pit.tax:.2f} PLN")
        print(f"Różnica wspólnie vs osobno: {joint_tax_saving:.2f} PLN")
    print(f"VAT należny: {yearly['sales_vat']:.2f} PLN")
    print(f"VAT naliczony: {yearly['purchase_vat']:.2f} PLN")
    print(f"VAT do zapłaty: {yearly['vat_to_pay']:.2f} PLN")


def export_all_reports(
    monthly,
    delegations_monthly,
    other_costs_monthly,
    pit_monthly,
    health_monthly,
    yearly,
    pit_result,
    trips,
    delegation_costs,
    other_costs_total,
    pension_income,
    spouse_income,
    individual_pit,
    joint_pit,
    joint_tax_saving,
    health_contribution_total,
    year,
    out_dir,
):
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    monthly_report = out_dir / "report_monthly.csv"
    yearly_report = out_dir / "report_yearly.csv"
    excel_report = out_dir / "report_tax.xlsx"

    export_monthly_report(
        monthly,
        delegations_monthly,
        other_costs_monthly,
        pit_monthly,
        health_monthly,
        monthly_report,
    )

    export_yearly_report(
        year,
        len(trips),
        delegation_costs,
        other_costs_total,
        pension_income,
        spouse_income,
        individual_pit,
        joint_pit,
        joint_tax_saving,
        health_contribution_total,
        yearly,
        pit_result,
        yearly_report,
    )

    export_excel_report(
        monthly,
        delegations_monthly,
        other_costs_monthly,
        pit_monthly,
        health_monthly,
        yearly,
        pit_result,
        pension_income,
        spouse_income,
        individual_pit,
        joint_pit,
        joint_tax_saving,
        health_contribution_total,
        trips,
        year,
        excel_report,
    )

    print("\nZapisano raporty:")
    print(monthly_report)
    print(yearly_report)
    print(excel_report)


def health_contribution_income_basis_from_config(config):
    return config.get("health_contribution", {}).get("income_basis", PREVIOUS_MONTH)


def main():
    args = parse_args()
    config = load_config(args.config, require_jpk=not args.check_delegations)

    current_year = args.year or datetime.now().year
    current_month = args.month

    if config.get("delegations_csv"):
        all_trips = load_delegations_csv(config["delegations_csv"])
    elif config.get("trips_xml"):
        all_trips = load_voyages(Path(config["trips_xml"]))
    else:
        all_trips = []

    trips = [trip for trip in all_trips if trip_is_in_scope(trip, current_year, current_month)]

    if args.check_delegations:
        print_delegation_check_report(trips)
        return

    delegation_costs = sum_trip_costs(trips)
    delegations_monthly = sum_trip_costs_by_month(trips)

    _, monthly_all = sum_jpk_folder(config["jpk_folder"])
    monthly = filter_monthly(monthly_all, current_year, current_month)

    other_costs = load_other_costs(config.get("other_costs_csv", "data/other_costs.csv"))
    other_costs_monthly_all = sum_other_costs_by_month(other_costs)
    other_costs_monthly = filter_decimal_monthly(
        other_costs_monthly_all,
        current_year,
        current_month,
    )
    other_costs_total = sum(other_costs_monthly.values(), ZERO)

    yearly = build_yearly_summary(monthly)

    scenario = load_tax_scenario_from_config(config, current_year)
    settlement = calculate_annual_settlement(
        scenario=scenario,
        business_income=BusinessIncome(
            revenue=yearly["sales_net"],
            purchase_costs=yearly["purchase_net"],
            delegation_costs=delegation_costs,
            other_costs=other_costs_total,
        ),
    )
    pit_result = settlement.pit

    pit_monthly = build_pit_monthly(
        monthly,
        delegations_monthly,
        other_costs_monthly,
    )
    health_summary = calculate_health_contribution_monthly(
        monthly,
        delegations_monthly,
        other_costs_monthly,
        income_basis=health_contribution_income_basis_from_config(config),
    )

    print_delegations(trips)
    print_monthly_jpk(monthly)
    print_corrections(monthly)
    print_pit_monthly(pit_monthly)
    print_health_monthly(health_summary.monthly)
    print_yearly_summary(
        current_year,
        trips,
        delegation_costs,
        other_costs_total,
        settlement.pension_income,
        settlement.spouse_income,
        settlement.individual_pit,
        settlement.joint_pit,
        settlement.joint_tax_saving,
        health_summary.total,
        yearly,
        pit_result,
    )

    export_all_reports(
        monthly,
        delegations_monthly,
        other_costs_monthly,
        pit_monthly,
        health_summary.monthly,
        yearly,
        pit_result,
        trips,
        delegation_costs,
        other_costs_total,
        settlement.pension_income,
        settlement.spouse_income,
        settlement.individual_pit,
        settlement.joint_pit,
        settlement.joint_tax_saving,
        health_summary.total,
        current_year,
        args.out_dir,
    )


if __name__ == "__main__":
    try:
        main()
        print("\n=== TAX APP OK ===")
        sys.exit(0)
    except FileNotFoundError as error:
        print(f"\nBŁĄD PLIKU: {error}")
        sys.exit(2)
    except KeyError as error:
        print(f"\nBŁĄD KONFIGURACJI: {error}")
        sys.exit(3)
    except ValueError as error:
        print(f"\nBŁĄD DANYCH: {error}")
        sys.exit(2)
    except Exception as error:
        print(f"\nBŁĄD APLIKACJI: {error}")
        sys.exit(1)
