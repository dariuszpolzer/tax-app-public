from decimal import Decimal

from calculator_costs import sum_trip_costs


class DummyTrip:
    def __init__(self, cost):
        self.total_diet_pln = cost


def test_sum_trip_costs():
    trips = [
        DummyTrip(100),
        DummyTrip(200),
        DummyTrip(300),
    ]

    assert sum_trip_costs(trips) == Decimal("600.00")
