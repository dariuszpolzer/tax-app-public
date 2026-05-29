import csv
from dataclasses import dataclass, field
from datetime import date
from decimal import Decimal, InvalidOperation
from pathlib import Path

from config_loader import load_config, load_tax_scenario_from_config
from delegations_csv import load_delegations_csv
from jpk.calculator_jpk import find_jpk_files, month_from_filename
from jpk.parser_jpk import parse_jpk_v7m
from other_costs import load_other_costs
from parser_trips import load_voyages


@dataclass
class ValidationReport:
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    info: list[str] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return not self.errors


def _is_valid_month(value: str) -> bool:
    if len(value) != 7 or value[4] != "-":
        return False
    year, month = value.split("-")
    return year.isdigit() and month.isdigit() and 1 <= int(month) <= 12


def _check_date(value: str, label: str, report: ValidationReport) -> None:
    try:
        date.fromisoformat(value)
    except ValueError:
        report.errors.append(f"Nieprawidłowa data w {label}: {value}")


def _check_decimal(value: str, label: str, report: ValidationReport) -> None:
    try:
        Decimal(str(value).replace(",", "."))
    except InvalidOperation:
        report.errors.append(f"Nieprawidłowa kwota w {label}: {value}")


def validate_delegations_csv(path: str | Path, year: int, report: ValidationReport) -> None:
    csv_path = Path(path)
    required = {"date_to", "amount_pln"}

    with csv_path.open(newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f, delimiter=";")
        fieldnames = set(reader.fieldnames or [])
        missing = sorted(required - fieldnames)
        if missing:
            report.errors.append(
                f"Brak wymaganych kolumn w delegations_csv ({csv_path}): {', '.join(missing)}"
            )
            return

        rows_count = 0
        for row_number, row in enumerate(reader, start=2):
            rows_count += 1
            date_to = row.get("date_to", "")
            amount = row.get("amount_pln", "")
            if not date_to:
                report.errors.append(f"Brak date_to w delegations_csv, wiersz {row_number}")
            else:
                _check_date(date_to, f"delegations_csv wiersz {row_number}", report)
                if date_to[:4].isdigit() and int(date_to[:4]) != year:
                    report.warnings.append(
                        f"Delegacja z innego roku niż raport ({year}): wiersz {row_number}, {date_to}"
                    )
            if not amount:
                report.errors.append(f"Brak amount_pln w delegations_csv, wiersz {row_number}")
            else:
                _check_decimal(amount, f"delegations_csv wiersz {row_number}", report)

    trips = load_delegations_csv(csv_path)
    report.info.append(f"Delegacje CSV: {len(trips)} rekordów")
    if rows_count == 0:
        report.warnings.append(f"Plik delegations_csv jest pusty: {csv_path}")


def validate_other_costs_csv(path: str | Path, year: int, report: ValidationReport) -> None:
    csv_path = Path(path)
    if not csv_path.exists():
        report.info.append(f"Inne koszty: plik nie istnieje, przyjęto brak kosztów ({csv_path})")
        return

    required = {"date", "type", "description", "amount_pln"}
    with csv_path.open(newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f, delimiter=";")
        fieldnames = set(reader.fieldnames or [])
        missing = sorted(required - fieldnames)
        if missing:
            report.errors.append(
                f"Brak wymaganych kolumn w other_costs_csv ({csv_path}): {', '.join(missing)}"
            )
            return

        rows_count = 0
        for row_number, row in enumerate(reader, start=2):
            rows_count += 1
            cost_date = row.get("date", "")
            amount = row.get("amount_pln", "")
            if not cost_date:
                report.errors.append(f"Brak date w other_costs_csv, wiersz {row_number}")
            else:
                _check_date(cost_date, f"other_costs_csv wiersz {row_number}", report)
                if cost_date[:4].isdigit() and int(cost_date[:4]) != year:
                    report.warnings.append(
                        f"Inny koszt z innego roku niż raport ({year}): wiersz {row_number}, {cost_date}"
                    )
            if not amount:
                report.errors.append(f"Brak amount_pln w other_costs_csv, wiersz {row_number}")
            else:
                _check_decimal(amount, f"other_costs_csv wiersz {row_number}", report)

    costs = load_other_costs(csv_path)
    report.info.append(f"Inne koszty: {len(costs)} rekordów")
    if rows_count == 0:
        report.warnings.append(f"Plik other_costs_csv jest pusty: {csv_path}")


def validate_jpk_folder(path: str | Path, year: int, report: ValidationReport) -> None:
    folder = Path(path)
    files = find_jpk_files(str(folder))
    report.info.append(f"JPK: {len(files)} plików XML")

    for xml_path in files:
        data = parse_jpk_v7m(str(xml_path))
        month = month_from_filename(xml_path)
        if month == "unknown":
            month = data.get("period_month", "unknown")
        if not _is_valid_month(month):
            report.warnings.append(f"Nie ustalono miesiąca JPK: {xml_path}")
            continue
        if int(month[:4]) != year:
            report.warnings.append(f"JPK z innego roku niż raport ({year}): {xml_path} -> {month}")


def validate_config_data(path: str | Path, year: int, require_jpk: bool = True) -> ValidationReport:
    report = ValidationReport()

    try:
        config = load_config(path, require_jpk=require_jpk)
        report.info.append(f"Config: {Path(path)}")
        load_tax_scenario_from_config(config, year)
    except Exception as error:
        report.errors.append(str(error))
        return report

    if config.get("delegations_csv"):
        try:
            validate_delegations_csv(config["delegations_csv"], year, report)
        except Exception as error:
            report.errors.append(f"Błąd delegations_csv: {error}")
    elif config.get("trips_xml"):
        try:
            trips = load_voyages(Path(config["trips_xml"]))
            report.info.append(f"Delegacje XML legacy: {len(trips)} rekordów")
        except Exception as error:
            report.errors.append(f"Błąd trips_xml: {error}")
    else:
        report.info.append("Delegacje: brak źródła, przyjęto 0 rekordów")

    if require_jpk:
        try:
            validate_jpk_folder(config["jpk_folder"], year, report)
        except Exception as error:
            report.errors.append(f"Błąd JPK: {error}")

    validate_other_costs_csv(config.get("other_costs_csv", "data/other_costs.csv"), year, report)
    return report
