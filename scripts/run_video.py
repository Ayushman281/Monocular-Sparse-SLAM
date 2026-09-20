#!/usr/bin/env python3
"""Standalone proof of concept using the identical backend preprocessing and native runner."""
import argparse
import asyncio
import json
import shutil
import sys
import time
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend"))


async def main():
    from app.config import Settings
    from app.camera import CameraOptions
    from app.jobs import JobManager
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--video", type=Path, required=True)
    parser.add_argument("--camera", type=Path, help="JSON produced by calibrate_camera.py")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    settings = Settings.load()
    settings.guard()
    if args.video.stat().st_size > settings.max_bytes:
        parser.error("Video exceeds upload size limit")
    if args.output.exists():
        parser.error("Choose a new output directory; existing results are never overwritten")
    settings.jobs.mkdir(parents=True, exist_ok=True)
    options = CameraOptions.model_validate_json(args.camera.read_text()) if args.camera else CameraOptions()
    manager = JobManager(settings)
    job = manager.reserve()
    shutil.copyfile(args.video, job.directory / "input.video")
    await manager.run(job, options, time.perf_counter())
    # Retain proof-of-concept diagnostics explicitly in the requested folder.
    shutil.copytree(job.directory, args.output)
    print(json.dumps(job.public(), indent=2))
    manager.remove(job)
    if job.state != "success":
        raise SystemExit(1)


if __name__ == "__main__":
    asyncio.run(main())
