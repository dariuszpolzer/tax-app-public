import csv
from datetime import date
from decimal import Decimal
from pathlib import Path

from models import Trip


def parse_decimal(value) -> Decimal:
    return Decimal(str(value or "0.00").replace(",", "."))


def parse_date(value):
    if not value:
        return None
    return date.fromisoformat(value)


def load_delegations_csv(path) -> list[Trip]:
    csv_path = Path(path)

    if not csv_path.exists():
        raise FileNotFoundError(f"Nie istnieje plik delegacji CSV: {csv_path}")

    trips = []

    with open(csv_path, newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f, delimiter=";")

        for index, row in enumerate(reader, start=1):
            date_from = parse_date(row.get("date_from"))
            date_to = parse_date(row.get("date_to")) or date_from
            amount_pln = parse_decimal(row.get("amount_pln"))
            year = int(row.get("year") or (date_to or date_from).year)

            trips.append(
                Trip(
                    nr_del=row.get("number") or f"CSV/{index}/{year}",
                    employee=row.get("employee") or "",
                    purpose_city=row.get("city") or "",
                    purpose_desc=row.get("description") or "",
                    transport=row.get("transport") or "",
                    advance=Decimal("0.00"),
                    currency="PLN",
                    date_from=date_from,
                    date_to=date_to,
                    year=year,
                    signed_at=None,
                    proofs_count=0,
                    test=str(row.get("test") or "false").lower() == "true",
                    created_at=None,
                    iters=[],
                    diets=[],
                    total_diet_pln=amount_pln,
                )
            )

    return trips


def export_delegations_csv(trips, out_file):
    out_path = Path(out_file)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    with open(out_path, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.writer(f, delimiter=";")
        writer.writerow(
            [
                "number",
                "date_from",
                "date_to",
                "year",
                "city",
                "description",
                "transport",
                "employee",
                "amount_pln",
                "test",
            ]
        )

        for trip in trips:
            writer.writerow(
                [
                    trip.nr_del,
                    trip.date_from.isoformat() if trip.date_from else "",
                    trip.date_to.isoformat() if trip.date_to else "",
                    trip.year,
                    trip.purpose_city,
                    trip.purpose_desc,
                    trip.transport,
                    trip.employee,
                    f"{trip.total_diet_pln:.2f}",
                    str(trip.test).lower(),
                ]
            )
