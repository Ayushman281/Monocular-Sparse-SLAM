"""One configuration contract for AWS and Lightning. Disabled by default."""
import os
import platform
from dataclasses import dataclass
from pathlib import Path


def number(name: str, default: float, low: float, high: float) -> float:
    value = float(os.getenv(name, str(default)))
    if not low <= value <= high:
        raise ValueError(f"{name} must be between {low} and {high}")
    return value


@dataclass(frozen=True)
class Settings:
    target: str
    enabled: bool
    runner: Path
    vocab: Path
    jobs: Path
    max_bytes: int
    max_duration: float
    fps: float
    width: int
    fov: float
    min_area: int
    levels: int
    fast: int
    display_points: int
    concurrency: int
    timeout: float
    ttl: float
    max_jobs: int

    @classmethod
    def load(cls):
        return cls(
            os.getenv("EXECUTION_TARGET", "disabled"),
            os.getenv("ENABLE_SLAM", "false").lower() == "true",
            Path(os.getenv("SLAM_RUNNER", "/opt/slam/bin/slam_runner")),
            Path(os.getenv("SLAM_VOCAB", "/opt/slam/share/orb_vocab.fbow")),
            Path(os.getenv("JOB_ROOT", "/tmp/slam-jobs")),
            int(number("MAX_VIDEO_SIZE_MB", 200, 1, 500) * 1024**2),
            number("MAX_VIDEO_DURATION_SECONDS", 30, 10, 120),
            number("TARGET_PROCESSING_FPS", 15, 5, 30),
            int(number("MAX_PROCESSING_WIDTH", 640, 320, 1280)),
            number("DEFAULT_HORIZONTAL_FOV_DEGREES", 65, 20, 140),
            int(number("ORB_MIN_AREA", 800, 100, 5000)),
            int(number("ORB_NUM_LEVELS", 8, 1, 12)),
            int(number("FAST_THRESHOLD", 20, 1, 100)),
            int(number("MAX_DISPLAY_POINTS", 10000, 100, 20000)),
            int(number("MAX_CONCURRENT_SLAM_JOBS", 1, 1, 4)),
            number("SLAM_PROCESS_TIMEOUT_SECONDS", 90, 10, 300),
            number("JOB_TTL_SECONDS", 1800, 60, 86400),
            int(number("MAX_RETAINED_JOBS", 10, 1, 100)),
        )

    def guard(self):
        if self.target not in {"aws", "lightning"} or not self.enabled:
            raise RuntimeError("Select EXECUTION_TARGET=aws|lightning and ENABLE_SLAM=true on the hosted runtime.")
        if platform.system() != "Linux" or "microsoft" in platform.release().lower():
            raise RuntimeError("Backend execution is restricted to hosted Linux, not Windows or WSL.")
