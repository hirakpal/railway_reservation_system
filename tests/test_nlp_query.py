# tests/test_nlp_query.py
from nlp_query_processor import parse_nl_query


def test_parse_basic_position():
    prefs = parse_nl_query("I want an aisle seat near the entrance")
    assert prefs.get("position") == "aisle"
    assert prefs.get("near") == "entrance"


def test_parse_seat_ids_and_range():
    prefs = parse_nl_query("Seats 2-4 please")
    assert prefs.get("seat_ids") == [2, 3, 4]

