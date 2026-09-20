import json
import math
import shutil
from fractions import Fraction
from pathlib import Path
from .config import Settings
from .errors import JobError
from .process import run_process


def metadata_from_probe(data: dict, settings: Settings, target_fps: float | None = None) -> dict:
    streams = [s for s in data.get("streams", []) if s.get("codec_type") == "video"
               and not s.get("disposition", {}).get("attached_pic")]
    if len(streams) != 1:
        raise JobError("Upload a file containing exactly one RGB video stream.")
    stream = streams[0]
    allowed_containers = {"mov", "mp4", "m4a", "3gp", "3g2", "mj2", "matroska", "webm", "avi"}
    if not set(data.get("format", {}).get("format_name", "").split(",")) & allowed_containers:
        raise JobError("Use an MP4, MOV, AVI or WebM video container.")
    if stream.get("codec_name") not in {"h264", "hevc", "vp8", "vp9", "av1", "mpeg4", "mjpeg"}:
        raise JobError("The video codec is unsupported. Export as H.264 MP4.")
    try:
        width, height = int(stream["width"]), int(stream["height"])
        duration = float(stream.get("duration") or data["format"]["duration"])
        fps = float(Fraction(stream.get("avg_frame_rate", "0/1")))
        sar = stream.get("sample_aspect_ratio", "1:1")
        if sar not in {"1:1", "N/A", "0:1"}:
            raise JobError("Anamorphic pixels are unsupported; export square-pixel video.")
        rotation = float(stream.get("tags", {}).get("rotate", 0))
        for side in stream.get("side_data_list", []):
            if "rotation" in side:
                rotation = float(side["rotation"])
        if not math.isfinite(rotation) or abs(rotation / 90 - round(rotation / 90)) > .001:
            raise JobError("Unsupported orientation. Export a video with 0/90/180/270-degree rotation.")
        rotation = round(rotation) % 360
    except (KeyError, ValueError, TypeError, ZeroDivisionError, OverflowError) as exc:
        raise JobError("Video metadata is missing or corrupt.") from exc
    if not math.isfinite(duration) or not 0.2 <= duration <= settings.max_duration:
        raise JobError(f"Video duration must be between 0.2 and {settings.max_duration:g} seconds.")
    if not math.isfinite(fps) or not .5 <= fps <= 240:
        raise JobError("Cannot determine a supported video frame rate.")
    if not (16 <= width <= 8192 and 16 <= height <= 8192 and width * height <= 34_000_000):
        raise JobError("Input resolution is outside supported limits.")
    display_w, display_h = (height, width) if rotation in {90, 270} else (width, height)
    # Bound both axes for portrait videos as well as landscape; preserve aspect ratio.
    scale = min(1.0, settings.width / max(display_w, display_h))
    w, h = max(16, round(display_w * scale / 2) * 2), max(16, round(display_h * scale / 2) * 2)
    if min(display_w * scale, display_h * scale) < 16:
        raise JobError("Video aspect ratio is too extreme.")
    processed_fps = min(fps, target_fps or settings.fps, settings.fps)
    return {"duration_seconds": duration, "input_width": width, "input_height": height,
            "input_fps": fps, "frame_count": int(stream["nb_frames"]) if str(stream.get("nb_frames", "")).isdigit() else None,
            "rotation_degrees": rotation, "display_width": display_w, "display_height": display_h,
            "processing_width": w, "processing_height": h, "processed_fps": processed_fps,
            "codec": stream["codec_name"]}


async def probe(video: Path, settings: Settings, target_fps: float | None = None) -> dict:
    output = video.parent / "probe.json"
    with output.open("wb") as handle:
        code = await run_process([
            "ffprobe", "-v", "error", "-protocol_whitelist", "file,pipe", "-show_streams", "-show_format",
            "-of", "json", str(video),
        ], video.parent / "media.log", 10, stdout=handle)
    if code or output.stat().st_size > 1024 * 1024:
        raise JobError("This file cannot be read as a valid video.")
    try:
        return metadata_from_probe(json.loads(output.read_text()), settings, target_fps)
    except json.JSONDecodeError as exc:
        raise JobError("Cannot read video metadata.") from exc


async def normalize(video: Path, meta: dict, settings: Settings) -> Path:
    """FFmpeg autorotates once; lossless FFV1 produces bounded CFR frames for C++."""
    target = video.parent / "normalized.mkv"
    raw_budget = 4 * meta["processing_width"] * meta["processing_height"] * math.ceil(meta["duration_seconds"] * meta["processed_fps"] + 2)
    if shutil.disk_usage(video.parent).free < raw_budget + 128 * 1024**2:
        raise JobError("Insufficient temporary space for this clip at the configured resolution.", "storage_full")
    vf = (f"fps={meta['processed_fps']:.10f},"
          f"scale={meta['processing_width']}:{meta['processing_height']}:flags=area,setsar=1")
    code = await run_process([
        "ffmpeg", "-hide_banner", "-loglevel", "error", "-xerror", "-nostdin", "-y",
        "-protocol_whitelist", "file,pipe", "-threads", "2", "-i", str(video),
        "-map", "0:v:0", "-an", "-sn", "-dn", "-t", str(settings.max_duration + .1),
        "-vf", vf, "-fps_mode", "cfr", "-c:v", "ffv1", "-level", "1", "-threads", "2",
        "-pix_fmt", "bgr0", "-map_metadata", "-1", str(target),
    ], video.parent / "media.log", settings.timeout)
    if code or not target.exists() or target.stat().st_size == 0:
        raise JobError("Video decoding failed. Re-export the clip as H.264 MP4.")
    return target
