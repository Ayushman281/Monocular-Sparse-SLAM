import asyncio
import json
import logging
import shutil
import time
from dataclasses import dataclass, field
from pathlib import Path
from uuid import uuid4
import yaml
from .camera import CameraOptions, camera_config
from .config import Settings
from .errors import JobError
from .process import run_process
from .results import parse_results
from .video import normalize, probe


@dataclass
class Job:
    id: str
    directory: Path
    created: float = field(default_factory=time.time)
    state: str = "uploading"
    stage: str = "Uploading"
    result: dict | None = None
    error: str | None = None
    error_code: str | None = None
    completed: float | None = None
    task: asyncio.Task | None = None

    def public(self):
        return {"job_id": self.id, "status": self.state, "stage": self.stage,
                "error": self.error, "error_code": self.error_code, "result": self.result}


class JobManager:
    def __init__(self, settings: Settings):
        self.settings = settings
        self.jobs: dict[str, Job] = {}
        self.active: set[str] = set()

    def reserve(self) -> Job:
        # This method has no await: admission and insertion are atomic on the one event loop.
        if len(self.active) >= self.settings.concurrency:
            raise JobError("The server is processing another upload. Try again shortly.", "busy")
        self.cleanup()
        if len(self.jobs) >= self.settings.max_jobs:
            completed = [j for j in self.jobs.values() if j.completed is not None]
            if not completed:
                raise JobError("The server is busy. Try again shortly.", "busy")
            self.remove(min(completed, key=lambda j: j.completed))
        if shutil.disk_usage(self.settings.jobs).free < 2 * 1024**3:
            raise JobError("The server has insufficient temporary storage.", "storage_full")
        job_id = uuid4().hex
        directory = self.settings.jobs / job_id
        directory.mkdir(mode=0o700)
        job = Job(job_id, directory)
        self.jobs[job_id] = job
        self.active.add(job_id)
        return job

    def remove(self, job: Job):
        # Direct children with server-generated UUID names only.
        if job.id in self.active:
            return
        shutil.rmtree(job.directory, ignore_errors=True)
        self.jobs.pop(job.id, None)

    def cleanup(self):
        now = time.time()
        for job in list(self.jobs.values()):
            if job.completed and now - job.completed >= self.settings.ttl:
                self.remove(job)
        # Clean orphan directories left by server restart; never active folders.
        for child in self.settings.jobs.iterdir():
            if (child.is_dir() and len(child.name) == 32
                    and all(c in "0123456789abcdef" for c in child.name)
                    and child.name not in self.jobs and now - child.stat().st_mtime >= self.settings.ttl):
                shutil.rmtree(child, ignore_errors=True)

    async def run(self, job: Job, options: CameraOptions, accepted: float):
        try:
            async with asyncio.timeout(self.settings.timeout):
                job.state, job.stage = "processing", "Preparing video"
                preprocessing_start = time.perf_counter()
                video = job.directory / "input.video"
                meta = await probe(video, self.settings, options.target_fps)
                config = camera_config(options, meta, self.settings)
                (job.directory / "camera.yaml").write_text(yaml.safe_dump(config))
                normalized = await normalize(video, meta, self.settings)
                prep_seconds = time.perf_counter() - preprocessing_start
                job.stage = "Tracking camera and optimizing map"
                runner_start = time.perf_counter()
                code = await run_process([
                    str(self.settings.runner), "--video", str(normalized),
                    "--config", str(job.directory / "camera.yaml"), "--vocab", str(self.settings.vocab),
                    "--output", str(job.directory), "--no-viewer", "--drain-timeout", str(min(30, self.settings.timeout)),
                ], job.directory / "slam.log", self.settings.timeout)
                native_seconds = time.perf_counter() - runner_start
                if code == 2:
                    raise JobError("SLAM could not establish a stable map. Use more camera translation, textured surfaces, slower motion and better lighting.", "tracking_failed")
                if code:
                    raise JobError("The native SLAM process failed. Try a different video.", "native_failure")
                job.stage = "Preparing visualization"
                post_start = time.perf_counter()
                result = await asyncio.to_thread(parse_results, job.directory, self.settings.display_points)
                if abs(result["slam"]["frames_processed"] - meta["duration_seconds"] * meta["processed_fps"]) > 2:
                    raise JobError("The decoded frame count differs from the video duration. Re-export the clip.", "incomplete_video")
                # Include removal of both video copies in measured server processing.
                video.unlink(missing_ok=True)
                normalized.unlink(missing_ok=True)
                processing = {"preprocessing_seconds": prep_seconds, "slam_process_seconds": native_seconds,
                              "postprocessing_seconds": 0.0, "processing_time_seconds": 0.0,
                              "real_time_factor": 0.0, "target_met": False}
                result.update({"status": "success", "video": meta, "processing": processing,
                               "camera": {"mode": options.mode, "parameters": config["Camera"]},
                               "warnings": ["Monocular reconstruction has arbitrary global scale."] +
                               (["Intrinsics are approximated from FOV; this may reduce trajectory and map accuracy."]
                                if options.mode == "approximate" else []),
                               "job_id": job.id})
                if result["slam"]["frames_tracked"] < .7 * result["slam"]["frames_processed"]:
                    result["warnings"].append("Tracking was unavailable for more than 30% of sampled frames; inspect trajectory coverage before using this map.")
                # Time a complete result serialization and file write before freezing timing fields.
                result_path = job.directory / "result.json"
                result_path.write_text(json.dumps(result, allow_nan=False, separators=(",", ":")))
                processing["postprocessing_seconds"] = time.perf_counter() - post_start
                processing["processing_time_seconds"] = time.perf_counter() - accepted
                processing["real_time_factor"] = processing["processing_time_seconds"] / meta["duration_seconds"]
                processing["target_met"] = processing["processing_time_seconds"] <= 10 and processing["real_time_factor"] <= 1
                result_path.write_text(json.dumps(result, allow_nan=False, separators=(",", ":")))
                job.result = result
                job.state, job.stage = "success", "Reconstruction ready"
        except asyncio.CancelledError:
            job.state, job.error_code, job.error = "failed", "cancelled", "Server stopped during processing. Upload again."
            raise
        except TimeoutError:
            job.state, job.error_code, job.error = "failed", "timeout", "Processing exceeded the server time limit."
        except JobError as exc:
            job.state, job.error_code, job.error = "failed", exc.code, str(exc)
        except ValueError as exc:
            job.state, job.error_code, job.error = "failed", "invalid_calibration", str(exc)
        except Exception:
            logging.getLogger(__name__).exception("SLAM job %s failed", job.id)
            job.state, job.error_code, job.error = "failed", "internal_error", "Processing failed. Try another clip."
        finally:
            for name in ("input.video", "normalized.mkv"):
                (job.directory / name).unlink(missing_ok=True)
            if job.state == "failed":
                job.stage = "Processing stopped"
            job.completed = time.time()
            self.active.discard(job.id)

    async def close(self):
        tasks = [j.task for j in self.jobs.values() if j.task and not j.task.done()]
        for task in tasks:
            task.cancel()
        await asyncio.gather(*tasks, return_exceptions=True)
