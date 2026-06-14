"""
NLP query processor - extended to recognize seat position words and simple numeric ranges.
"""
import os
import re
from typing import Dict, Any

OPENAI_ENABLED = bool(os.environ.get("OPENAI_API_KEY"))


def parse_nl_query(text: str) -> Dict[str, Any]:
    text_l = (text or "").lower()
    prefs: Dict[str, Any] = {}
    if "aisle" in text_l:
        prefs["position"] = "aisle"
    elif "window" in text_l:
        prefs["position"] = "window"
    elif "middle" in text_l or "center" in text_l:
        prefs["position"] = "middle"

    if "entrance" in text_l:
        prefs["near"] = "entrance"
    if "exit" in text_l or "door" in text_l:
        prefs["near"] = "exit"

    # extract explicit seat ids mentioned like "seat 3" or "seats 2 and 3"
    ids = re.findall(r"seat[s]?\s*(\d+)", text_l)
    if ids:
        prefs["seat_ids"] = [int(i) for i in ids]

    # simple numeric ranges: "seats 2-4"
    range_match = re.search(r"seats?\s*(\d+)\s*-\s*(\d+)", text_l)
    if range_match:
        a = int(range_match.group(1)); b = int(range_match.group(2))
        prefs["seat_ids"] = list(range(a, b + 1))

    return prefs


if __name__ == "__main__":
    print(parse_nl_query("I want an aisle seat near the entrance and seat 3"))
