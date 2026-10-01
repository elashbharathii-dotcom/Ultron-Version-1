"""
Direct terminal control — with a hard blocklist and timeout.
This runs on your REAL OS (not sandboxed). Use sandbox_tool.py instead
whenever you're executing model-GENERATED code rather than a command
you explicitly want run.
"""
import subprocess
import psutil
from config import SHELL_BLOCKLIST, SHELL_TIMEOUT_SECONDS


def run_command(command: str) -> dict:
    lowered = command.lower()
    for banned in SHELL_BLOCKLIST:
        if banned.lower() in lowered:
            return {"success": False, "stdout": "", "stderr": f"Blocked: command matches banned pattern '{banned}'", "exit_code": -1}

    try:
        result = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True,
            timeout=SHELL_TIMEOUT_SECONDS,
        )
        return {
            "success": result.returncode == 0,
            "stdout": result.stdout[-4000:],
            "stderr": result.stderr[-4000:],
            "exit_code": result.returncode,
        }
    except subprocess.TimeoutExpired:
        return {"success": False, "stdout": "", "stderr": "Command timed out", "exit_code": -1}
    except Exception as e:
        return {"success": False, "stdout": "", "stderr": str(e), "exit_code": -1}


def system_status() -> dict:
    """CPU / RAM / disk / network snapshot for the dashboard and for the model."""
    net = psutil.net_io_counters()
    return {
        "cpu_percent": psutil.cpu_percent(interval=0.3),
        "ram_percent": psutil.virtual_memory().percent,
        "ram_used_gb": round(psutil.virtual_memory().used / 1e9, 2),
        "ram_total_gb": round(psutil.virtual_memory().total / 1e9, 2),
        "disk_percent": psutil.disk_usage("/").percent,
        "net_sent_mb": round(net.bytes_sent / 1e6, 1),
        "net_recv_mb": round(net.bytes_recv / 1e6, 1),
        "process_count": len(psutil.pids()),
    }


def list_processes(limit=15):
    procs = sorted(
        psutil.process_iter(["pid", "name", "cpu_percent", "memory_percent"]),
        key=lambda p: p.info.get("cpu_percent") or 0,
        reverse=True,
    )
    return [p.info for p in procs[:limit]]
