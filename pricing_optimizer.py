# pricing_optimizer.py
"""
A tiny dynamic pricing module. It computes a suggested price per seat based on
current booking levels. This is illustrative — adjust logic for production.
"""
from typing import List, Tuple, Dict

BASE_PRICE = 100.0


def optimize_pricing(seat_data: List[Tuple[int, str, str]]) -> Dict[int, float]:
    """Return a mapping seat_id -> price.

    seat_data is a list of tuples (seat_id, status, user_id)
    """
    total = len(seat_data)
    booked = sum(1 for _id, status, _u in seat_data if status == "booked")
    occupancy = booked / total if total else 0

    prices = {}
    for seat_id, status, _ in seat_data:
        price = BASE_PRICE
        # simple surge: if occupancy > 0.6, increase price
        if occupancy > 0.8:
            price *= 1.5
        elif occupancy > 0.6:
            price *= 1.25
        elif occupancy > 0.4:
            price *= 1.1

        # make already booked seats show a higher 'last price'
        if status == "booked":
            price *= 1.05

        prices[seat_id] = round(price, 2)
    return prices


if __name__ == "__main__":
    print(optimize_pricing([(1, "available", None), (2, "booked", "u1")]))
