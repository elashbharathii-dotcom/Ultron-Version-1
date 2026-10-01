"""
Runs model-generated Python code in an isolated environment.

Two modes:
  - Docker mode (preferred): runs inside a throwaway python:3.11-slim
    container with no network and a memory/CPU cap. Nothing can touch
    your real filesystem.
  - Fallback mode: if Docker isn't installed, runs in a temp folder with
    a short timeout. This is NOT a real security boundary — install
    Docker Desktop for real isolation.

Also exposes `run_and_repair`, which feeds stderr back to the LLM and
retries up to `max_attempts` times — this is the "dynamic script repair"
piece from your spec.
"""
import subprocess
import tempfile
import os
import shutil
import uuid

DOCKER_IMAGE = "python:3.11-slim"


def _docker_available() -> bool:
    return shutil.which("docker") is not None


def run_code(code: str, timeout: int = 20) -> dict:
    work_dir = tempfile.mkdtemp(prefix="ultron_sandbox_")
    script_path = os.path.join(work_dir, "script.py")
    with open(script_path, "w", encoding="utf-8") as f:
        f.write(code)

    try:
        if _docker_available():
            container_name = f"ultron_{uuid.uuid4().hex[:8]}"
            cmd = [
                "docker", "run", "--rm",
                "--name", container_name,
                "--network", "none",          # no internet access from sandboxed code
                "--memory", "512m",
                "--cpus", "1",
                "-v", f"{work_dir}:/sandbox:ro",
                DOCKER_IMAGE,
                "python", "/sandbox/script.py",
            ]
        else:
            cmd = ["python", script_path]

        result = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        return {
            "success": result.returncode == 0,
            "stdout": result.stdout[-4000:],
            "stderr": result.stderr[-4000:],
            "exit_code": result.returncode,
            "isolated": _docker_available(),
        }
    except subprocess.TimeoutExpired:
        return {"success": False, "stdout": "", "stderr": "Execution timed out", "exit_code": -1, "isolated": _docker_available()}
    finally:
        shutil.rmtree(work_dir, ignore_errors=True)


def run_and_repair(llm_fix_fn, code: str, max_attempts: int = 3) -> dict:
    """
    llm_fix_fn(broken_code, error_message) -> new_code_string
    Runs code, and on failure asks the LLM to fix it, up to max_attempts times.
    """
    attempt = 0
    current_code = code
    history = []
    while attempt < max_attempts:
        result = run_code(current_code)
        history.append({"attempt": attempt + 1, "code": current_code, "result": result})
        if result["success"]:
            result["attempts"] = history
            return result
        current_code = llm_fix_fn(current_code, result["stderr"])
        attempt += 1
    result["attempts"] = history
    return result
