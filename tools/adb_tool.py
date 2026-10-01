"""
Android Debug Bridge control.
Prereqs: platform-tools installed, phone has USB debugging enabled
(Settings > About phone > tap Build number 7x > Developer options >
USB debugging), and phone connected via USB (or ADB over Wi-Fi).
"""
import subprocess
from config import ADB_PATH


def _adb(*args, timeout=15):
    try:
        result = subprocess.run(
            [ADB_PATH, *args], capture_output=True, text=True, timeout=timeout
        )
        return {"success": result.returncode == 0, "stdout": result.stdout.strip(), "stderr": result.stderr.strip()}
    except FileNotFoundError:
        return {"success": False, "stdout": "", "stderr": "adb not found — install Android platform-tools and add to PATH"}
    except subprocess.TimeoutExpired:
        return {"success": False, "stdout": "", "stderr": "adb command timed out"}


def list_devices():
    return _adb("devices", "-l")


def device_telemetry(serial: str = None):
    """Battery, screen state, and basic device info."""
    prefix = ["-s", serial] if serial else []
    battery = _adb(*prefix, "shell", "dumpsys", "battery")
    screen = _adb(*prefix, "shell", "dumpsys", "power")
    model = _adb(*prefix, "shell", "getprop", "ro.product.model")
    return {"battery": battery["stdout"], "model": model["stdout"], "power_raw": screen["stdout"][:500]}


def unlock_screen(serial: str = None, swipe: bool = True):
    prefix = ["-s", serial] if serial else []
    _adb(*prefix, "shell", "input", "keyevent", "224")  # wake up
    if swipe:
        _adb(*prefix, "shell", "input", "swipe", "300", "1000", "300", "300")
    return {"success": True}


def launch_app(package_name: str, serial: str = None):
    """e.g. package_name='com.whatsapp'"""
    prefix = ["-s", serial] if serial else []
    return _adb(*prefix, "shell", "monkey", "-p", package_name, "-c", "android.intent.category.LAUNCHER", "1")


def tap(x: int, y: int, serial: str = None):
    prefix = ["-s", serial] if serial else []
    return _adb(*prefix, "shell", "input", "tap", str(x), str(y))


def swipe(x1, y1, x2, y2, duration_ms=300, serial: str = None):
    prefix = ["-s", serial] if serial else []
    return _adb(*prefix, "shell", "input", "swipe", str(x1), str(y1), str(x2), str(y2), str(duration_ms))


def type_text(text: str, serial: str = None):
    prefix = ["-s", serial] if serial else []
    escaped = text.replace(" ", "%s")
    return _adb(*prefix, "shell", "input", "text", escaped)


def shell(raw_command: str, serial: str = None):
    """Escape hatch for any other `adb shell` command."""
    prefix = ["-s", serial] if serial else []
    return _adb(*prefix, "shell", raw_command)
