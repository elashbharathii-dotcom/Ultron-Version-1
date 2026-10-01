"""
Offline speech-to-text using faster-whisper.
Set WHISPER_DEVICE=cuda in your .env to use the RTX 5050 (much faster).
"""
import sounddevice as sd
import numpy as np
import tempfile
import wave
from faster_whisper import WhisperModel
from config import WHISPER_MODEL_SIZE, WHISPER_DEVICE

_model = None


def _get_model():
    global _model
    if _model is None:
        compute_type = "float16" if WHISPER_DEVICE == "cuda" else "int8"
        _model = WhisperModel(WHISPER_MODEL_SIZE, device=WHISPER_DEVICE, compute_type=compute_type)
    return _model


def record_audio(seconds: int = 5, samplerate: int = 16000) -> str:
    """Records from the default mic and returns a path to a temp WAV file."""
    audio = sd.rec(int(seconds * samplerate), samplerate=samplerate, channels=1, dtype="int16")
    sd.wait()
    tmp = tempfile.NamedTemporaryFile(suffix=".wav", delete=False)
    with wave.open(tmp.name, "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(samplerate)
        wf.writeframes(audio.tobytes())
    return tmp.name


def transcribe(audio_path: str) -> str:
    model = _get_model()
    segments, _ = model.transcribe(audio_path, beam_size=5)
    return " ".join(seg.text.strip() for seg in segments)


def listen_and_transcribe(seconds: int = 5) -> str:
    path = record_audio(seconds)
    return transcribe(path)
