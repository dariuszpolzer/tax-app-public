from decimal import Decimal
from pathlib import Path

from calculator_costs import sum_trip_costs, sum_trip_costs_by_month
from parser_trips import load_voyages


def test_load_vba_delegations_reference_totals():
    trips = load_voyages(Path("tests/data/vba_delegations_2026.xml"))

    assert len(trips) == 6
    assert [trip.nr_del for trip in trips] == [
        "T001/2026",
        "T002/2026",
        "T003/2026",
        "T004/2026",
        "T005/2026",
        "T006/2026",
    ]

    totals = {trip.nr_del: trip.total_diet_pln for trip in trips}

    assert totals == {
        "T001/2026": Decimal("6055.63"),
        "T002/2026": Decimal("67.5"),
        "T003/2026": Decimal("4035.36"),
        "T004/2026": Decimal("4915.98"),
        "T005/2026": Decimal("3825.91"),
        "T006/2026": Decimal("2153.13"),
    }
    assert sum_trip_costs(trips) == Decimal("21053.51")


def test_vba_delegations_are_integrated_into_monthly_costs():
    trips = load_voyages(Path("tests/data/vba_delegations_2026.xml"))

    assert sum_trip_costs_by_month(trips) == {
        "2026-01": Decimal("6055.63"),
        "2026-02": Decimal("4102.86"),
        "2026-03": Decimal("4915.98"),
        "2026-04": Decimal("3825.91"),
        "2026-05": Decimal("2153.13"),
    }


def test_translationems_root_is_supported(tmp_path):
    source = """<?xml version="1.0" encoding="UTF-8"?>
<Translationems>
  <Voyage NrDel="T005/2026" Pracownik="Jan Testowy" Cel="Brunsbüttel" Powód="Rozmowy handlowe" Transport="samochód służbowy" Zaliczka="0" Waluta="PLN" Od="2026-04-12" Do="2026-04-30" Rok="2026" DataPodpisu="2026-04-08" Ilość_Dowodów="0" Test="true" Created="2026-05-01T19:09:20">
    <Voy><Nr>1</Nr><Wyliczenie_diety Kraj="Niemcy" Waluta="EUR" Stawka="49" Jednostki="18.3333333333333"><Kwota_diety>898.33</Kwota_diety></Wyliczenie_diety><Waluta Kurs_waluty="4.2589" Data_waluty="2026-04-30" Tabela_waluty="A083Z260430"/><Dieta_PLN>3825.91</Dieta_PLN></Voy>
  </Voyage>
</Translationems>
"""
    path = tmp_path / "single_translationems.xml"
    path.write_text(source, encoding="utf-8")

    trips = load_voyages(path)

    assert len(trips) == 1
    assert trips[0].nr_del == "T005/2026"
    assert trips[0].test is True
    assert trips[0].total_diet_pln == Decimal("3825.91")
