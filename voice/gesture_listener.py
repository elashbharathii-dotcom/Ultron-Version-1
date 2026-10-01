"""
Run this as a SEPARATE, always-on script, alongside app.py and
wake_listener.py. It watches your webcam and measures how much motion
is happening in front of it — faster hand movement = faster orb spin.
It also tracks whether the brightest/most-moving region trends upward
or downward over time, to detect a swipe gesture (used to cycle panels
in the dashboard, since true page-scrolling isn't reliable from inside
a sandboxed browser component).

This uses simple frame-difference motion detection (not true hand-
skeleton tracking) because MediaPipe, the usual hand-tracking library,
doesn't yet reliably support very new Python versions like 3.14. This
is less precise (it reacts to ANY movement in frame, not specifically
your hand) but far more reliable to install and run.

Writes live state to data/gesture_state.json:
    {"speed_mult": 0.0-3.0, "swipe": "up" | "down" | null, "ts": <time>}

Run it with:
    python voice\\gesture_listener.py
Stop it with Ctrl+C. Requires a working webcam (index 0 by default).
"""
import cv2
import json
import os
import sys
import time
import collections
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import DATA_DIR

STATE_PATH = os.path.join(DATA_DIR, "gesture_state.json")
CAMERA_INDEX = 0
SMOOTHING = 0.7  # higher = smoother/slower to react, lower = twitchier
SWIPE_HISTORY_LEN = 8
SWIPE_MIN_TRAVEL = 60      # pixels of vertical travel to count as a swipe
SWIPE_COOLDOWN_SEC = 1.5


def _write_state(speed_mult: float, swipe):
    os.makedirs(DATA_DIR, exist_ok=True)
    with open(STATE_PATH, "w") as f:
        json.dump({"speed_mult": round(speed_mult, 2), "swipe": swipe, "ts": time.time()}, f)


def main():
    cap = cv2.VideoCapture(CAMERA_INDEX)
    if not cap.isOpened():
        print(f"Could not open webcam (index {CAMERA_INDEX}). "
              f"Check it's not in use by another app, or try CAMERA_INDEX = 1.")
        return

    print("Gesture listener running. Move your hand in front of the camera to speed up the orb.")
    print("Ctrl+C to stop.")

    ret, prev_frame = cap.read()
    if not ret:
        print("Couldn't read from webcam.")
        return
    prev_gray = cv2.cvtColor(prev_frame, cv2.COLOR_BGR2GRAY)
    prev_gray = cv2.GaussianBlur(prev_gray, (21, 21), 0)

    smoothed_speed = 0.0
    centroid_history = collections.deque(maxlen=SWIPE_HISTORY_LEN)
    last_swipe_time = 0.0

    try:
        while True:
            ret, frame = cap.read()
            if not ret:
                time.sleep(0.1)
                continue

            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            gray = cv2.GaussianBlur(gray, (21, 21), 0)

            diff = cv2.absdiff(prev_gray, gray)
            motion_amount = float(np.mean(diff))  # 0 (still) .. ~30+ (lots of motion)

            # Track the vertical center of the moving region (for swipe detection).
            _, thresh = cv2.threshold(diff, 25, 255, cv2.THRESH_BINARY)
            ys, xs = np.nonzero(thresh)
            swipe = None
            if len(ys) > 200:  # enough motion pixels to trust the centroid
                centroid_y = float(np.mean(ys))
                centroid_history.append(centroid_y)
                if len(centroid_history) == SWIPE_HISTORY_LEN:
                    travel = centroid_history[-1] - centroid_history[0]
                    now = time.time()
                    if abs(travel) > SWIPE_MIN_TRAVEL and (now - last_swipe_time) > SWIPE_COOLDOWN_SEC:
                        swipe = "down" if travel > 0 else "up"
                        last_swipe_time = now
                        centroid_history.clear()

            prev_gray = gray

            target_speed = min(3.0, motion_amount / 6.0)
            smoothed_speed = SMOOTHING * smoothed_speed + (1 - SMOOTHING) * target_speed

            _write_state(smoothed_speed, swipe)
            time.sleep(0.1)  # ~10 updates/sec is plenty for this purpose

    except KeyboardInterrupt:
        print("\nStopping gesture listener.")
    finally:
        cap.release()


if __name__ == "__main__":
    main()
