"""
Reads any new command captured by voice/wake_listener.py and marks it
consumed. Import this into app.py.
"""
import json
import os
from config import DATA_DIR

QUEUE_PATH = os.path.join(DATA_DIR, "wake_queue.json")


def get_pending_wake_command():
    """Returns the oldest un-consumed command text, or None if there isn't one."""
    if not os.path.exists(QUEUE_PATH):
        return None
    try:
        with open(QUEUE_PATH, "r") as f:
            queue = json.load(f)
    except Exception:
        return None

    for entry in queue:
        if not entry.get("consumed"):
            entry["consumed"] = True
            with open(QUEUE_PATH, "w") as f:
                json.dump(queue, f)
            return entry["text"]
    return None
