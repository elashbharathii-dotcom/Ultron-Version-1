"""
Reads the live hand-motion state written by voice/gesture_listener.py.
Import this into app.py.
"""
import json
import os
import time
from config import DATA_DIR

STATE_PATH = os.path.join(DATA_DIR, "gesture_state.json")
STALE_AFTER_SEC = 2.0  # if the listener isn't running, don't use old data


def get_gesture_state():
    """Returns {"speed_mult": float, "swipe": "up"/"down"/None} — defaults if unavailable."""
    if not os.path.exists(STATE_PATH):
        return {"speed_mult": 1.0, "swipe": None}
    try:
        with open(STATE_PATH, "r") as f:
            data = json.load(f)
    except Exception:
        return {"speed_mult": 1.0, "swipe": None}

    if time.time() - data.get("ts", 0) > STALE_AFTER_SEC:
        return {"speed_mult": 1.0, "swipe": None}

    return {"speed_mult": data.get("speed_mult", 1.0), "swipe": data.get("swipe")}


def consume_swipe():
    """Reads and clears the swipe flag so it only triggers a panel change once."""
    state = get_gesture_state()
    swipe = state.get("swipe")
    if swipe and os.path.exists(STATE_PATH):
        try:
            with open(STATE_PATH, "r") as f:
                data = json.load(f)
            data["swipe"] = None
            with open(STATE_PATH, "w") as f:
                json.dump(data, f)
        except Exception:
            pass
    return swipe
