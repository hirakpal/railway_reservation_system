"""
Enhanced GenAI recommender with optional OpenAI integration and use of seat metadata.
The recommender accepts a list of available seats which can be:
  - list of ints: [1,2,3]
  - list of tuples/rows: [(seat_id, status, user_id, position), ...]

If OPENAI_API_KEY is set in env, the module will call OpenAI's chat completion API
to request a ranked list of seat ids. Otherwise it falls back to a lightweight
heuristic that uses seat metadata (position, row) if available.
"""
import os
import json
from typing import List, Dict, Any, Tuple

OPENAI_ENABLED = bool(os.environ.get("OPENAI_API_KEY"))
if OPENAI_ENABLED:
    try:
        import openai
    except Exception:
        OPENAI_ENABLED = False


def _normalize_seats(available_seats: List[Any]) -> List[Dict[str, Any]]:
    """Normalize different seat representations into list of dicts.

    Supported input shapes:
      - [1,2,3]
      - [(1, 'available', None, 'aisle'), ...]
      - [{'seat_id':1, 'position':'aisle', ...}, ...]
    """
    out = []
    for s in available_seats:
        if isinstance(s, dict):
            out.append(s)
        elif isinstance(s, tuple) or isinstance(s, list):
            # try to map common tuple shapes
            # (seat_id, status, user_id) or (seat_id, status, user_id, position)
            if len(s) >= 1:
                seat = {"seat_id": s[0]}
                if len(s) >= 2:
                    seat["status"] = s[1]
                if len(s) >= 3:
                    seat["user_id"] = s[2]
                if len(s) >= 4:
                    seat["position"] = s[3]
                out.append(seat)
        elif isinstance(s, int):
            out.append({"seat_id": s})
        else:
            # skip unknown
            continue
    return out


def _heuristic_rank(seats: List[Dict[str, Any]], preferences: Dict[str, Any]) -> List[int]:
    def score(seat: Dict[str, Any]) -> float:
        s = 0.0
        pos_pref = preferences.get("position")
        if pos_pref and seat.get("position"):
            if pos_pref == seat.get("position"):
                s += 10.0
        # proximity to entrance heuristic: lower seat_id == nearer entrance
        near = preferences.get("near")
        if near == "entrance":
            s += max(0, 5 - (seat.get("seat_id", 0)))
        # friends proximity if provided
        friends = preferences.get("friends") or []
        if friends and seat.get("seat_id") is not None:
            s += -min(abs(seat["seat_id"] - f) for f in friends)
        # prefer lower seat_id as tiebreaker
        s += 1.0 / (1 + seat.get("seat_id", 0))
        return s

    ranked = sorted(seats, key=lambda x: score(x), reverse=True)
    return [s["seat_id"] for s in ranked]


def recommend_seats(available_seats: List[Any], preferences: Dict[str, Any], top_n: int = 3) -> List[int]:
    """Return a ranked list of recommended seat_ids.

    If OpenAI is enabled, call the model with a prompt describing seats and
    preferences and request a JSON array of seat ids ranked by preference.
    Otherwise fall back to the heuristic.
    """
    seats = _normalize_seats(available_seats)
    if not seats:
        return []

    if OPENAI_ENABLED:
        try:
            # Build a concise prompt with seat metadata
            seat_lines = []
            for s in seats:
                parts = [f"id={s.get('seat_id')}"]
                if s.get("position"):
                    parts.append(f"position={s.get('position')}")
                seat_lines.append(";".join(parts))
            prompt = (
                "You are a seat recommendation assistant.\n"
                f"Available seats:\n{chr(10).join(seat_lines)}\n\n"
                f"User preferences: {json.dumps(preferences)}\n"
                "Return a JSON array containing seat ids in order of recommended preference, e.g. [3,1,2]."
                " Do not add any other text."
            )
            # use chat completion
            resp = openai.ChatCompletion.create(
                model=os.environ.get("OPENAI_MODEL", "gpt-3.5-turbo"),
                messages=[{"role": "user", "content": prompt}],
                max_tokens=256,
                temperature=0.0,
            )
            content = resp["choices"][0]["message"]["content"].strip()
            # parse JSON from response
            parsed = json.loads(content)
            if isinstance(parsed, list):
                return [int(x) for x in parsed][:top_n]
        except Exception:
            # fall back to heuristic on any failure
            pass

    ranked = _heuristic_rank(seats, preferences)
    return ranked[:top_n]


if __name__ == "__main__":
    # small demo
    print(recommend_seats([1, 2, 3, 4, 5], {"position": "aisle"}))
