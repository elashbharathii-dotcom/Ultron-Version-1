"""
Run this as a SEPARATE, always-on script (in its own terminal window),
alongside `streamlit run app.py`. It listens continuously through your
microphone for either:
  - something close to "hey ultron" (fuzzy-matched voice wake word), or
  - a CLAP (a short, sharp sound spike)
Either one triggers Ultron to record and capture your next spoken command.
"""
import time
import json
import os
import sys
import difflib
import sounddevice as sd
import numpy as np
import wave
import tempfile
from faster_whisper import WhisperModel

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import WHISPER_DEVICE, DATA_DIR

QUEUE_PATH = os.path.join(DATA_DIR, "wake_queue.json")
WAKE_TARGETS = ["hey ultron", "hi ultron", "ultron"]
FUZZY_THRESHOLD = 0.55
CHUNK_SECONDS = 3.5
COMMAND_SECONDS = 6
SAMPLE_RATE = 16000

# Clap detection tuning: a clap is a short, sharp burst much louder than
# the recent background noise level.
CLAP_PEAK_MULTIPLIER = 4.0
CLAP_MIN_PEAK = 0.15   # ignore quiet rooms entirely below this raw level
_noise_floor = 0.01    # adapts over time

print("Loading models (this may take a moment the first time)...")
_compute = "float16" if WHISPER_DEVICE == "cuda" else "int8"
_wake_model = WhisperModel("tiny", device=WHISPER_DEVICE, compute_type=_compute)
_command_model = WhisperModel("base", device=WHISPER_DEVICE, compute_type=_compute)
print("Ready. Listening for 'Hey Ultron' or a CLAP... (Ctrl+C to stop)")


def _record(seconds: int):
    """Returns (wav_path, raw_audio_array)."""
    audio = sd.rec(int(seconds * SAMPLE_RATE), samplerate=SAMPLE_RATE, channels=1, dtype="int16")
    sd.wait()
    tmp = tempfile.NamedTemporaryFile(suffix=".wav", delete=False)
    with wave.open(tmp.name, "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(SAMPLE_RATE)
        wf.writeframes(audio.tobytes())
    return tmp.name, audio


def _transcribe(path: str, model: WhisperModel) -> str:
    segments, _ = model.transcribe(path, beam_size=1)
    return " ".join(seg.text.strip() for seg in segments).lower()


def _looks_like_hallucination(text: str) -> bool:
    words = text.split()
    if len(words) < 4:
        return False
    chunk = " ".join(words[:max(1, len(words) // 3)])
    return text.count(chunk) >= 2


def _is_wake_phrase(heard: str) -> bool:
    if not heard.strip():
        return False
    words = heard.replace(",", " ").replace(".", " ").split()
    for n in range(1, min(4, len(words)) + 1):
        for i in range(len(words) - n + 1):
            phrase = " ".join(words[i:i + n])
            for target in WAKE_TARGETS:
                ratio = difflib.SequenceMatcher(None, phrase, target).ratio()
                if ratio >= FUZZY_THRESHOLD:
                    return True
    return "tron" in heard


def _is_clap(audio: np.ndarray) -> bool:
    """A clap = a short loud spike much louder than the ambient noise floor,
    with most of the clip staying quiet (distinguishes it from continuous speech)."""
    global _noise_floor
    samples = audio.astype(np.float32) / 32768.0
    abs_samples = np.abs(samples.flatten())

    window = max(1, int(0.05 * SAMPLE_RATE))  # 50ms windows
    n_windows = len(abs_samples) // window
    if n_windows < 3:
        return False
    peaks = [abs_samples[i * window:(i + 1) * window].max() for i in range(n_windows)]

    overall_peak = max(peaks)
    loud_windows = sum(1 for p in peaks if p > overall_peak * 0.6)

    is_clap = (
        overall_peak > CLAP_MIN_PEAK
        and overall_peak > _noise_floor * CLAP_PEAK_MULTIPLIER
        and loud_windows <= 3  # short burst, not sustained like speech
    )

    quiet_peaks = [p for p in peaks if p < overall_peak * 0.3]
    if quiet_peaks:
        _noise_floor = 0.9 * _noise_floor + 0.1 * (sum(quiet_peaks) / len(quiet_peaks))

    return is_clap


def _push_to_queue(text: str):
    os.makedirs(DATA_DIR, exist_ok=True)
    entry = {"text": text, "ts": time.time(), "consumed": False}
    queue = []
    if os.path.exists(QUEUE_PATH):
        try:
            with open(QUEUE_PATH, "r") as f:
                queue = json.load(f)
        except Exception:
            queue = []
    queue.append(entry)
    with open(QUEUE_PATH, "w") as f:
        json.dump(queue, f)


def _capture_command():
    print("Speak your command NOW...")
    cmd_path, _ = _record(COMMAND_SECONDS)
    command_text = _transcribe(cmd_path, _command_model)
    os.unlink(cmd_path)
    if command_text.strip() and not _looks_like_hallucination(command_text):
        print(f"Command captured: {command_text}")
        _push_to_queue(command_text)
    else:
        print("Didn't catch a real command (silence or noise) — going back to listening.")


def main():
    while True:
        try:
            clip_path, raw_audio = _record(CHUNK_SECONDS)

            if _is_clap(raw_audio):
                os.unlink(clip_path)
                print("\n👏 Clap detected!")
                _capture_command()
                continue

            heard = _transcribe(clip_path, _wake_model)
            os.unlink(clip_path)
            print("Heard:", repr(heard))

            if _is_wake_phrase(heard):
                print(f"\nWake word heard ('{heard.strip()}')")
                _capture_command()

        except KeyboardInterrupt:
            print("\nStopping wake-word listener.")
            break
        except Exception as e:
            print(f"(non-fatal error, continuing) {e}")
            time.sleep(1)


if __name__ == "__main__":
    main()
