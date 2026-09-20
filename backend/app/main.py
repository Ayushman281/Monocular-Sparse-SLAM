import asyncio
import os
import time
from contextlib import asynccontextmanager, suppress
from pathlib import Path
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import ValidationError
from starlette.datastructures import UploadFile
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.formparsers import MultiPartException
from .camera import CameraOptions
from .config import Settings
from .errors import JobError
from .jobs import JobManager
from .provenance import source_revision


class BodyLimit:
    def __init__(self, app, limit: int):
        self.app, self.limit = app, limit

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            return await self.app(scope, receive, send)
        headers = dict(scope.get("headers", []))
        try:
            length = int(headers.get(b"content-length", b"0"))
        except ValueError:
            return await JSONResponse({"detail": "Invalid content length"}, 400)(scope, receive, send)
        if length < 0 or length > self.limit:
            return await JSONResponse({"detail": "Video upload is too large"}, 413)(scope, receive, send)
        received = 0

        async def limited_receive():
            nonlocal received
            message = await receive()
            received += len(message.get("body", b""))
            if received > self.limit:
                # Starlette closes partially spooled files for a multipart error.
                scope.setdefault("state", {})["upload_too_large"] = True
                raise MultiPartException("Video upload is too large")
            return message

        await self.app(scope, limited_receive, send)


def create_app(settings: Settings | None = None):
    settings = settings or Settings.load()
    manager = JobManager(settings)
    revision = source_revision()

    @asynccontextmanager
    async def lifespan(app):
        settings.guard()
        settings.jobs.mkdir(parents=True, exist_ok=True, mode=0o700)
        manager.cleanup()

        async def janitor():
            while True:
                await asyncio.sleep(30)
                manager.cleanup()

        cleanup = asyncio.create_task(janitor())
        try:
            yield
        finally:
            cleanup.cancel()
            with suppress(asyncio.CancelledError):
                await cleanup
            await manager.close()

    app = FastAPI(title="Monocular Sparse SLAM", lifespan=lifespan, docs_url="/api/docs", openapi_url="/api/openapi.json")
    app.state.manager = manager
    app.add_middleware(BodyLimit, limit=settings.max_bytes + 65536)

    def ready():
        return settings.runner.is_file() and os.access(settings.runner, os.X_OK) and settings.vocab.is_file()

    @app.get("/api/health")
    async def health():
        return {"status": "healthy" if ready() else "not_ready", "slam_runner_available": ready(),
                "execution_target": settings.target, "slam_enabled": settings.enabled}

    @app.get("/api/system")
    async def system():
        return {"slam_engine": "stella_vslam", "engine_version": "0.7.0", "processing_mode": "cpu",
                "application_revision": revision,
                "max_duration_seconds": settings.max_duration, "max_video_size_mb": settings.max_bytes / 1024**2,
                "target_fps": settings.fps, "max_processing_width": settings.width,
                "job_ttl_seconds": settings.ttl, "scale": "arbitrary"}

    @app.post("/api/v1/slam/process", status_code=202)
    async def process(request: Request):
        if not ready():
            raise HTTPException(503, "The SLAM engine or vocabulary is not installed on this server.")
        try:
            job = manager.reserve()
        except JobError as exc:
            raise HTTPException(429 if exc.code == "busy" else 507, str(exc)) from exc
        started = False
        try:
            async with asyncio.timeout(120):
                async with request.form(max_files=1, max_fields=1, max_part_size=16384) as form:
                    upload = form.get("video")
                    raw_options = form.get("camera", "{}")
                    if not isinstance(upload, UploadFile) or not isinstance(raw_options, str):
                        raise HTTPException(422, "Provide a video file and optional camera JSON.")
                    if len(raw_options) > 16384:
                        raise HTTPException(422, "Camera configuration is too large.")
                    try:
                        options = CameraOptions.model_validate_json(raw_options)
                    except ValidationError as exc:
                        raise HTTPException(422, "Invalid camera settings: " + exc.errors()[0]["msg"]) from exc
                    written = 0
                    with (job.directory / "input.video").open("wb") as output:
                        while chunk := await upload.read(1024 * 1024):
                            written += len(chunk)
                            if written > settings.max_bytes:
                                raise HTTPException(413, "Video upload is too large.")
                            output.write(chunk)
                    if written == 0:
                        raise HTTPException(422, "The uploaded video is empty.")
            accepted = time.perf_counter()
            job.task = asyncio.create_task(manager.run(job, options, accepted))
            started = True
            return {"job_id": job.id, "status": "accepted", "status_url": f"/api/v1/slam/{job.id}"}
        except TimeoutError as exc:
            raise HTTPException(408, "Video upload timed out.") from exc
        except StarletteHTTPException as exc:
            if getattr(request.state, "upload_too_large", False):
                raise HTTPException(413, "Video upload is too large.") from exc
            raise
        finally:
            if not started:
                manager.active.discard(job.id)
                manager.remove(job)

    def find_job(job_id: str):
        manager.cleanup()
        job = manager.jobs.get(job_id)
        if job is None:
            raise HTTPException(404, "Result not found or expired. Upload the video again.")
        return job

    @app.get("/api/v1/slam/{job_id}")
    async def status(job_id: str):
        return JSONResponse(find_job(job_id).public(), headers={"Cache-Control": "no-store"})

    @app.get("/api/v1/slam/{job_id}/{artifact}")
    async def download(job_id: str, artifact: str):
        mime = {"trajectory.csv": "text/csv", "pointcloud.ply": "application/octet-stream", "result.json": "application/json"}
        if artifact not in mime:
            raise HTTPException(404, "Unknown artifact")
        job = find_job(job_id)
        if job.state != "success":
            raise HTTPException(409, "The reconstruction is not ready.")
        return FileResponse(job.directory / artifact, media_type=mime[artifact], filename=artifact)

    # Optional single-port/static deployments can still mount compiled assets.
    # Lightning's two-service launcher points FRONTEND_DIR at a nonexistent path.
    @app.get("/app-config.json", include_in_schema=False)
    async def frontend_config():
        return JSONResponse({"preview": False, "apiBase": ""}, headers={"Cache-Control": "no-store"})

    @app.get("/api/{unknown:path}", include_in_schema=False)
    async def unknown_api(unknown: str):
        raise HTTPException(404, "Unknown API endpoint")

    frontend = Path(os.getenv("FRONTEND_DIR", "frontend/dist"))
    if frontend.is_dir():
        app.mount("/", StaticFiles(directory=frontend, html=True), name="frontend")
    return app
