# nlp_query_processor.py
"""
Very small Natural Language -> structured query parser.
This is intentionally lightweight so it works offline. Optionally you can plug
in an LLM call (OpenAI) if you have an API key.
"""
import os
import re
from typing import Dict, Any

OPENAI_ENABLED = bool(os.environ.get("OPENAI_API_KEY"))


def parse_nl_query(text: str) -> Dict[str, Any]:
    """Parse a user NL query into a preferences dict used by the recommender.

    Examples:
      - "I want an aisle seat near the entrance"
      - "Show me window seats"
    """
    text_l = text.lower()
    prefs: Dict[str, Any] = {}
    if "aisle" in text_l:
        prefs["position"] = "aisle"
    elif "window" in text_l:
        prefs["position"] = "window"
    elif "middle" in text_l:
        prefs["position"] = "middle"

    if "entrance" in text_l:
        prefs["near"] = "entrance"
    if "exit" in text_l or "door" in text_l:
        prefs["near"] = "exit"

    # extract explicit seat ids mentioned like "seat 3" or "seats 2 and 3"
    ids = re.findall(r"seat[s]?\s*(\d+)", text_l)
    if ids:
        prefs["seat_ids"] = [int(i) for i in ids]

    return prefs


if __name__ == "__main__":
    print(parse_nl_query("I want an aisle seat near the entrance and seat 3"))
