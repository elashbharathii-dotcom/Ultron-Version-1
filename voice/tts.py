"""
Offline text-to-speech using pyttsx3 (wraps Windows SAPI5 / macOS NSSpeech / espeak on Linux).
"""
import pyttsx3
from config import TTS_RATE

_engine = None


def _get_engine():
    global _engine
    if _engine is None:
        _engine = pyttsx3.init()
        _engine.setProperty("rate", TTS_RATE)
    return _engine


def speak(text: str):
    engine = _get_engine()
    engine.say(text)
    engine.runAndWait()
