#!/usr/bin/env python3
"""Repeated real HTTP benchmark. Run on the SAME hosted machine as the server."""
import argparse
import hashlib
import json
import os
import platform
import statistics
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))


def command(*args):
    try:
        return subprocess.check_output(args, cwd=ROOT, text=True, stderr=subprocess.DEVNULL, timeout=10).strip()
    except (OSError, subprocess.SubprocessError):
        return "unavailable"


def main():
    from app.config import Settings
    Settings.load().guard()
    import httpx
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--video", type=Path, required=True)
    parser.add_argument("--camera", type=Path)
    parser.add_argument("--runs", type=int, default=5)
    parser.add_argument("--url", default="http://127.0.0.1:8000")
    parser.add_argument("--official", action="store_true")
    parser.add_argument("--output", type=Path, default=Path("benchmarks/runs"))
    args = parser.parse_args()
    if not 1 <= args.runs <= 20 or (args.official and args.runs < 5):
        parser.error("Use 1–20 runs, at least 5 for the official benchmark")
    git_sha = command("git", "rev-parse", "HEAD")
    dirty = command("git", "status", "--porcelain")
    if args.official and (git_sha == "unavailable" or dirty != ""):
        parser.error("Official benchmark requires a clean committed checkout")
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    output = args.output / stamp
    output.mkdir(parents=True, exist_ok=False)
    camera = args.camera.read_text() if args.camera else "{}"
    with args.video.open("rb") as handle:
        video_sha256 = hashlib.file_digest(handle, "sha256").hexdigest()
    environment = {
        "date_utc": stamp, "git_commit": git_sha, "git_dirty": bool(dirty),
        "machine": platform.machine(), "os": platform.platform(), "vcpus": os.cpu_count(),
        "cpu": command("lscpu"), "memory": Path("/proc/meminfo").read_text(),
        "docker_version": command("docker", "--version"),
        "execution_target": os.getenv("EXECUTION_TARGET"),
        "video_sha256": video_sha256,
        "video_name": args.video.name,
        "engine_lock": (ROOT / "slam/dependencies.env").read_text(),
        "patch_sha256": hashlib.sha256((ROOT / "slam/patches/offline-drain.patch").read_bytes()).hexdigest(),
        "settings": {k: os.getenv(k) for k in ("OMP_NUM_THREADS", "TARGET_PROCESSING_FPS", "MAX_PROCESSING_WIDTH", "ORB_MIN_AREA")},
    }
    (output / "environment.json").write_text(json.dumps(environment, indent=2))
    records, failures = [], []
    with httpx.Client(base_url=args.url.rstrip("/"), timeout=150) as client:
        environment["server_system"] = client.get("/api/system").json()
        if args.official and environment["server_system"].get("application_revision") != git_sha:
            parser.error("The running server revision does not match this benchmark checkout. Rebuild/restart it first.")
        (output / "environment.json").write_text(json.dumps(environment, indent=2))
        for run in range(1, args.runs + 1):
            start = time.perf_counter()
            with args.video.open("rb") as handle:
                response = client.post("/api/v1/slam/process", files={"video": (args.video.name, handle, "application/octet-stream")}, data={"camera": camera})
            response.raise_for_status()
            accepted = time.perf_counter()
            job_id = response.json()["job_id"]
            while True:
                status_response = client.get(f"/api/v1/slam/{job_id}")
                status_response.raise_for_status()
                status = status_response.json()
                if status["status"] in {"success", "failed"}:
                    break
                if time.perf_counter() - accepted > 330:
                    raise TimeoutError("No terminal job status")
                time.sleep(.05)  # HTTP status polling only, never frame playback.
            done = time.perf_counter()
            (output / f"run-{run}.json").write_text(json.dumps(status, indent=2))
            if status["status"] != "success":
                failures.append({"run": run, "error": status["error"]})
                print(f"Run {run}: FAILED — {status['error']}")
                continue
            result = status["result"]
            elapsed = result["processing"]["processing_time_seconds"]
            records.append({"run": run, "server_seconds": elapsed,
                            "observed_result_ready_seconds": done-accepted,
                            "upload_accept_seconds": accepted-start,
                            "duration_seconds": result["video"]["duration_seconds"],
                            "rtf": result["processing"]["real_time_factor"],
                            "slam_seconds": result["processing"]["slam_process_seconds"], **result["slam"]})
            print(f"Run {run}: server {elapsed:.3f}s, observed ready {done-accepted:.3f}s, RTF {result['processing']['real_time_factor']:.3f}")
        values = [r["server_seconds"] for r in records]
        summary = {"runs": records, "failures": failures, "official_requested": args.official,
                   "mean": statistics.mean(values) if values else None,
                   "median": statistics.median(values) if values else None,
                   "min": min(values) if values else None, "max": max(values) if values else None,
                   "performance_gate_passed": bool(args.official and not failures and len(records) == args.runs and all(
                       9.9 <= r["duration_seconds"] <= 10.1 and r["server_seconds"] <= 10 and r["rtf"] <= 1
                       and r["observed_result_ready_seconds"] <= 10 for r in records))}
        (output / "summary.json").write_text(json.dumps(summary, indent=2))
        print(json.dumps({k:v for k,v in summary.items() if k not in {"runs"}}, indent=2))
        if failures or (args.official and not summary["performance_gate_passed"]):
            raise SystemExit(1)


if __name__ == "__main__":
    main()
