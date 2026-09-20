import csv
import json
import math
from pathlib import Path
import numpy as np
from .errors import JobError


def camera_center(tcw: np.ndarray) -> np.ndarray:
    """World-to-camera [R|t] -> camera center in world, Cw=-R.T@t."""
    pose = np.asarray(tcw, dtype=float)
    if pose.shape != (4, 4) or not np.isfinite(pose).all():
        raise ValueError("Pose must be a finite 4x4 transform")
    return -pose[:3, :3].T @ pose[:3, 3]


def read_tum(path: Path) -> list[list[float]]:
    rows = []
    if not path.exists():
        return rows
    for line in path.read_text().splitlines():
        if not line.strip() or line.startswith("#"):
            continue
        values = [float(x) for x in line.split()]
        if len(values) != 8 or not all(math.isfinite(x) for x in values):
            raise ValueError("Invalid trajectory row")
        if rows and values[0] <= rows[-1][0]:
            raise ValueError("Non-increasing trajectory timestamps")
        if abs(sum(q*q for q in values[4:]) - 1) > .002:
            raise ValueError("Invalid orientation quaternion")
        rows.append(values)
    return rows


def parse_results(directory: Path, max_points: int) -> dict:
    try:
        stats = json.loads((directory / "stats.json").read_text())
        if stats.get("pose_convention") != "Twc" or stats.get("scale") != "arbitrary" or stats.get("map_components") != 1:
            raise ValueError("Unexpected coordinate convention or multiple map components")
        if stats.get("status") != "success" or stats.get("optimization_complete") is not True:
            raise JobError("SLAM could not establish a stable map. Try more camera translation, textured surfaces and less blur.", "tracking_failed")
        trajectory = read_tum(directory / "trajectory.tum")
        keyframes = read_tum(directory / "keyframes.tum")
        if len(trajectory) < 3 or len(keyframes) < 2:
            raise ValueError("Insufficient valid camera poses")
        key_times = {round(p[0], 6) for p in keyframes}
        with (directory / "trajectory.csv").open("w", newline="") as handle:
            writer = csv.writer(handle)
            writer.writerow(["timestamp", "tx", "ty", "tz", "qx", "qy", "qz", "qw", "is_keyframe"])
            for pose in trajectory:
                writer.writerow([*pose, int(round(pose[0], 6) in key_times)])
        points = []
        with (directory / "landmarks.csv").open(newline="") as handle:
            for row in csv.DictReader(handle):
                point = [float(row[k]) for k in ("x", "y", "z")]
                if not all(math.isfinite(p) for p in point) or int(row["observations"]) < 2:
                    raise ValueError("Invalid exported landmark")
                points.append(point)
        if len(points) < 10 or len(points) != stats["map_points"]:
            raise ValueError("Empty or inconsistent map")
        if not 0 < stats["frames_tracked"] <= stats["frames_processed"]:
            raise ValueError("Inconsistent frame statistics")
        # Deterministic display subsampling; PLY retains all valid landmarks.
        selected = np.linspace(0, len(points)-1, min(max_points, len(points)), dtype=int)
        return {"slam": stats, "trajectory": trajectory, "keyframe_trajectory": keyframes,
                "points": [points[i] for i in selected], "display_point_count": len(selected),
                "trajectory_columns": ["timestamp", "tx", "ty", "tz", "qx", "qy", "qz", "qw"],
                "coordinate_convention": "Twc; x right, y down, z forward at initialization; arbitrary scale"}
    except JobError:
        raise
    except (ValueError, KeyError, TypeError, OSError) as exc:
        raise JobError("The SLAM output is incomplete or invalid. Try another clip.", "invalid_output") from exc
