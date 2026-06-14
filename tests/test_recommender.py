# tests/test_recommender.py
from genai_recommender import recommend_seats


def test_heuristic_recommendation():
    seats = [
        (1, 'available', None, 'window'),
        (2, 'available', None, 'aisle'),
        (3, 'available', None, 'middle'),
        (4, 'available', None, 'aisle'),
        (5, 'available', None, 'window'),
    ]
    prefs = {"position": "aisle"}
    recs = recommend_seats(seats, prefs, top_n=2)
    # Expect aisle seats (2 and 4) to be top, in some order
    assert 2 in recs and len(recs) == 2

