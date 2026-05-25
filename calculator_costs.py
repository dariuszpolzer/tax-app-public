from collections import defaultdict
from decimal import Decimal


def sum_trip_costs(trips):
    return sum(t.total_diet_pln for t in trips)


def sum_trip_costs_by_month(trips):
    monthly = defaultdict(lambda: Decimal("0.00"))

    for trip in trips:
        if trip.date_to:
            month = trip.date_to.strftime("%Y-%m")
        elif trip.date_from:
            month = trip.date_from.strftime("%Y-%m")
        elif trip.created_at:
            month = trip.created_at.strftime("%Y-%m")
        elif trip.iters and trip.iters[0].depart_at:
            month = trip.iters[0].depart_at.strftime("%Y-%m")
        else:
            month = f"{trip.year}-01"

        monthly[month] += Decimal(str(trip.total_diet_pln or 0))

    return monthly
