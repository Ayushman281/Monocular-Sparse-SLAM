import math
from typing import Literal
from pydantic import BaseModel, ConfigDict, Field, model_validator
from .config import Settings


class CameraOptions(BaseModel):
    model_config = ConfigDict(extra="forbid", allow_inf_nan=False)
    mode: Literal["approximate", "calibrated"] = "approximate"
    horizontal_fov: float | None = Field(None, ge=20, le=140)
    fx: float | None = Field(None, gt=0, le=100000)
    fy: float | None = Field(None, gt=0, le=100000)
    cx: float | None = Field(None, ge=0, le=16384)
    cy: float | None = Field(None, ge=0, le=16384)
    cols: int | None = Field(None, ge=16, le=16384)
    rows: int | None = Field(None, ge=16, le=16384)
    k1: float = Field(0, ge=-5, le=5)
    k2: float = Field(0, ge=-5, le=5)
    p1: float = Field(0, ge=-1, le=1)
    p2: float = Field(0, ge=-1, le=1)
    k3: float = Field(0, ge=-5, le=5)
    target_fps: float | None = Field(None, ge=5, le=30)

    @model_validator(mode="after")
    def calibrated_fields(self):
        if self.mode == "calibrated":
            if any(getattr(self, k) is None for k in ("fx", "fy", "cx", "cy", "cols", "rows")):
                raise ValueError("Calibrated mode requires fx, fy, cx, cy, cols and rows.")
            if self.cx >= self.cols or self.cy >= self.rows:
                raise ValueError("Principal point must be inside the calibration image.")
        return self


def camera_config(options: CameraOptions, meta: dict, settings: Settings) -> dict:
    w, h = meta["processing_width"], meta["processing_height"]
    source_w, source_h = meta["display_width"], meta["display_height"]
    if options.mode == "calibrated":
        if (options.cols, options.rows) != (source_w, source_h):
            raise ValueError("Calibration dimensions must match the video after orientation correction.")
        sx, sy = w / source_w, h / source_h
        fx, fy = options.fx * sx, options.fy * sy
        # OpenCV resize pixel-center convention; do not scale only focal lengths.
        cx, cy = (options.cx + .5) * sx - .5, (options.cy + .5) * sy - .5
    else:
        fx = fy = w / (2 * math.tan(math.radians(options.horizontal_fov or settings.fov) / 2))
        cx, cy = w / 2, h / 2
    return {
        "Camera": {"name": "uploaded-monocular", "setup": "monocular", "model": "perspective",
                   "fx": fx, "fy": fy, "cx": cx, "cy": cy,
                   **{k: getattr(options, k) if options.mode == "calibrated" else 0.0
                      for k in ("k1", "k2", "p1", "p2", "k3")},
                   "fps": meta["processed_fps"], "cols": w, "rows": h, "color_order": "BGR"},
        "Preprocessing": {"min_size": settings.min_area},
        "Feature": {"name": "ORB", "scale_factor": 1.2, "num_levels": settings.levels,
                    "ini_fast_threshold": settings.fast, "min_fast_threshold": min(7, settings.fast)},
        "Mapping": {"baseline_dist_thr_ratio": .02,
                    "enable_interruption_before_local_BA": False,
                    "enable_interruption_of_landmark_generation": False},
        "KeyframeInserter": {"wait_for_local_bundle_adjustment": True},
    }
