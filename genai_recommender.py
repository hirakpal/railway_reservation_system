# genai_recommender.py
"""
Simple GenAI-backed recommender for seat selection.
This module provides a fallback heuristic recommender and an optional OpenAI call
if OPENAI_API_KEY is present in env.
"""
import os
from typing import List, Dict, Any

OPENAI_ENABLED = bool(os.environ.get("OPENAI_API_KEY"))


def recommend_seats(available_seats: List[int], preferences: Dict[str, Any], top_n: int = 3) -> List[int]:
    """Return a ranked list of recommended seat_ids.

    preferences can include keys like:
      - position: 'aisle'|'window'|'middle'
      - near: 'entrance'|'exit'|'middle'
      - friends: List[int]  (seat ids of friends to sit near)

    If OpenAI is configured, you can extend this function to call a model and
    ask for recommendations. For now this uses a deterministic heuristic.
    """
    # Simple heuristic scoring
    def score(seat: int) -> int:
        s = 0
        pos = preferences.get("position")
        if pos == "aisle":
            s += 5 if seat % 2 == 1 else 0
        elif pos == "window":
            s += 5 if seat in (1, 6) else 0
        # preference to be near a particular seat
        near = preferences.get("near")
        if near == "entrance":
            s += max(0, 5 - seat)
        if preferences.get("friends"):
            # simple proximity score
            s += -min(abs(seat - f) for f in preferences.get("friends"))
        return s

    ranked = sorted(available_seats, key=lambda x: score(x), reverse=True)
    return ranked[:top_n]


if __name__ == "__main__":
    print(recommend_seats([1, 2, 3, 4, 5], {"position": "aisle"}))
