"""
Central configuration for Ultron.
Reads secrets from a local .env file (never commit this file to git).
"""
import os
from dotenv import load_dotenv

load_dotenv()

# --- LLM brain (Ollama, fully offline) ---
OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://localhost:11434")
# qwen2.5:7b-instruct is a good default for an 8GB-class laptop GPU (RTX 5050):
# supports tool calling and fits comfortably with 4-bit quantization.
MODEL_NAME = os.getenv("ULTRON_MODEL", "qwen2.5:7b-instruct")

# --- Paths ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
SQLITE_PATH = os.path.join(DATA_DIR, "ultron_history.db")
CHROMA_PATH = os.path.join(DATA_DIR, "chroma_store")

# --- Safety ---
# Commands containing any of these substrings are ALWAYS blocked, no matter what
# the model asks for. Keep this list long. This is your last line of defense.
SHELL_BLOCKLIST = [
    "rm -rf /", "rm -rf /*", "mkfs", "dd if=", ":(){ :|:& };:",
    "shutdown", "reboot", "format ", "del /f /s /q C:\\", "diskpart",
    "> /dev/sda", "chmod -R 777 /", "wget http", "curl http",  # block blind downloads-and-run
]
SHELL_TIMEOUT_SECONDS = 30

# --- ADB ---
ADB_PATH = os.getenv("ADB_PATH", "adb")  # assumes adb is on PATH

# --- Voice ---
WHISPER_MODEL_SIZE = os.getenv("WHISPER_MODEL_SIZE", "base")  # tiny/base/small/medium
WHISPER_DEVICE = os.getenv("WHISPER_DEVICE", "cpu")  # set to "cuda" to use your RTX 5050
TTS_RATE = 175
