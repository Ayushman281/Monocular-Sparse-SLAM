import os
import subprocess
from pathlib import Path


def source_revision() -> str:
    if os.getenv("APP_REVISION"):
        return os.environ["APP_REVISION"]
    try:
        return subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=Path(__file__).resolve().parents[2],
                                       text=True, stderr=subprocess.DEVNULL, timeout=3).strip()
    except (OSError, subprocess.SubprocessError):
        return "unrecorded"
