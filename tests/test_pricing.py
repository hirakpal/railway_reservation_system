# tests/test_pricing.py
from pricing_optimizer import optimize_pricing


def test_pricing_basic():
    seat_data = [(1, 'available', None), (2, 'booked', 'u1'), (3, 'available', None), (4, 'available', None), (5, 'booked', 'u2')]
    prices = optimize_pricing(seat_data)
    assert isinstance(prices, dict)
    assert set(prices.keys()) == {1,2,3,4,5}

