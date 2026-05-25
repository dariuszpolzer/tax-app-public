from datetime import date, datetime
from decimal import Decimal
from pathlib import Path

from parser_trips import load_voyages


def test_load_voyages_from_example_xml():
    trips = load_voyages(Path("tests/data/example_trips.xml"))

    assert len(trips) == 1

    trip = trips[0]

    assert trip.nr_del == "T004/2026"
    assert trip.employee == "Jan Testowy"
    assert trip.purpose_city == "Brunsbüttel"
    assert trip.transport == "samochód służbowy"
    assert trip.year == 2026
    assert trip.test is True

    assert trip.date_from == date(2026, 3, 1)
    assert trip.date_to == date(2026, 3, 25)
    assert trip.signed_at == date(2026, 2, 25)
    assert trip.created_at == datetime(2026, 3, 26, 12, 35, 22)

    assert len(trip.iters) == 2
    assert trip.iters[0].country == "Polska"
    assert trip.iters[1].country == "Niemcy"
    assert trip.iters[1].destination == "Brunsbüttel"

    assert len(trip.diets) == 2
    assert trip.diets[0].country == "Polska"

    diet = trip.diets[1]

    assert diet.country == "Niemcy"
    assert diet.currency == "EUR"
    assert diet.rate == Decimal("49")
    assert diet.units == Decimal("23.5")
    assert diet.amount == Decimal("1151.5")
    assert diet.fx_rate == Decimal("4.2692")
    assert diet.fx_date == date(2026, 3, 25)
    assert diet.fx_table == "058/A/NBP/2026"
    assert diet.amount_pln == Decimal("4915.98")

    assert trip.total_diet_pln == Decimal("4915.98")
