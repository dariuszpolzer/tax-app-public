from datetime import datetime
from decimal import Decimal
from pathlib import Path
from typing import Any

from defusedxml import ElementTree as ET

from models import Trip, TripIter, TripVoyDiet

DATE_FMT = "%Y-%m-%d"
DATE_FMT_PL = "%d.%m.%Y"

DATETIME_FMT = "%Y-%m-%d %H:%M"
DATETIME_FMT_PL = "%d.%m.%Y %H:%M:%S"

CREATED_FMT = "%Y-%m-%dT%H:%M:%S"


def parse_date(value: str | None):
    if not value or value.strip() in ("", "0"):
        return None

    value = value.strip()

    for fmt in ("%Y-%m-%d", "%d.%m.%Y"):
        try:
            return datetime.strptime(value, fmt).date()
        except ValueError:
            pass

    raise ValueError(f"Nieznany format daty: {value}")


def parse_dt(value: str | None, fmt: str | None = None):
    if not value or value.strip() in ("", "0"):
        return None

    value = value.strip()

    formats = []
    if fmt:
        formats.append(fmt)

    formats += [
        "%Y-%m-%d %H:%M",
        "%Y-%m-%d %H:%M:%S",
        "%d.%m.%Y %H:%M",
        "%d.%m.%Y %H:%M:%S",
        "%Y-%m-%dT%H:%M:%S",
    ]

    for f in formats:
        try:
            return datetime.strptime(value, f)
        except ValueError:
            pass

    raise ValueError(f"Nieznany format daty i czasu: {value}")

    value = value.strip()


def parse_float(value):
    if value is None or value == "":
        return Decimal("0")

    return Decimal(str(value))


def parse_trip(voyage_el: Any) -> Trip:
    nr_del = voyage_el.attrib.get("NrDel", "")
    employee = voyage_el.attrib.get("Pracownik", "")
    purpose_city = voyage_el.attrib.get("Cel", "")
    purpose_desc = voyage_el.attrib.get("Powód", "")
    transport = voyage_el.attrib.get("Transport", "")
    advance = parse_float(voyage_el.attrib.get("Zaliczka"))
    currency = voyage_el.attrib.get("Waluta", "")

    date_from = parse_date(voyage_el.attrib.get("Od"))
    date_to = parse_date(voyage_el.attrib.get("Do"))
    year = int(voyage_el.attrib.get("Rok") or 0)
    signed_at = parse_date(voyage_el.attrib.get("DataPodpisu"))
    proofs_count = int(voyage_el.attrib.get("Ilość_Dowodów") or 0)
    test = voyage_el.attrib.get("Test", "false").lower() == "true"
    created_at = parse_dt(voyage_el.attrib.get("Created"), CREATED_FMT)

    iters = []
    for iter_el in voyage_el.findall("Iter"):
        iters.append(
            TripIter(
                nr=int(iter_el.findtext("Nr") or 0),
                country=iter_el.findtext("Kraj") or "",
                start=iter_el.findtext("Start") or "",
                depart_at=parse_dt(iter_el.findtext("Wyjazd")),
                border_at=parse_dt(iter_el.findtext("Granica")),
                destination=iter_el.findtext("Cel") or "",
                arrive_at=parse_dt(iter_el.findtext("Przyjazd")),
                hours_diff=parse_float(iter_el.findtext("Różnica")),
            )
        )

    diets = []
    total_diet_pln = Decimal("0")

    for voy_el in voyage_el.findall("Voy"):
        nr = int(voy_el.findtext("Nr") or 0)
        diet_el = voy_el.find("Wyliczenie_diety")
        waluta_el = voy_el.find("Waluta")

        amount_pln = parse_float(voy_el.findtext("Dieta_PLN"))

        diets.append(
            TripVoyDiet(
                nr=nr,
                country=diet_el.attrib.get("Kraj", "") if diet_el is not None else "",
                currency=diet_el.attrib.get("Waluta", "") if diet_el is not None else "",
                rate=parse_float(diet_el.attrib.get("Stawka") if diet_el is not None else None),
                units=parse_float(diet_el.attrib.get("Jednostki") if diet_el is not None else None),
                amount=parse_float(
                    diet_el.findtext("Kwota_diety") if diet_el is not None else None
                ),
                fx_rate=parse_float(
                    waluta_el.attrib.get("Kurs_waluty") if waluta_el is not None else None
                ),
                fx_date=parse_date(
                    waluta_el.attrib.get("Data_waluty") if waluta_el is not None else None
                ),
                fx_table=waluta_el.attrib.get("Tabela_waluty", "") if waluta_el is not None else "",
                amount_pln=amount_pln,
            )
        )

        total_diet_pln += amount_pln

    return Trip(
        nr_del=nr_del,
        employee=employee,
        purpose_city=purpose_city,
        purpose_desc=purpose_desc,
        transport=transport,
        advance=advance,
        currency=currency,
        date_from=date_from,
        date_to=date_to,
        year=year,
        signed_at=signed_at,
        proofs_count=proofs_count,
        test=test,
        created_at=created_at,
        iters=iters,
        diets=diets,
        total_diet_pln=total_diet_pln,
    )


def load_voyages(path: Path):
    tree = ET.parse(path)
    root = tree.getroot()

    voyages = root.findall(".//Voyage")

    return [parse_trip(v) for v in voyages]
