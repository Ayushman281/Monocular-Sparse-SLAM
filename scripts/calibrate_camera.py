#!/usr/bin/env python3
"""Checkerboard calibration, only on the selected hosted Linux runtime."""
import argparse
import json
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend"))


def main():
    from app.config import Settings
    Settings.load().guard()
    import cv2
    import numpy as np
    import yaml
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, required=True, help="Folder of checkerboard images or video")
    parser.add_argument("--cols", type=int, default=9, help="Inner corners, not squares")
    parser.add_argument("--rows", type=int, default=6)
    parser.add_argument("--square-size", type=float, required=True, help="Physical checkerboard square size")
    parser.add_argument("--fps", type=float, default=30, help="FPS of the camera's target video")
    parser.add_argument("--output", type=Path, default=Path("camera.yaml"))
    args = parser.parse_args()
    if not (3 <= args.cols <= 30 and 3 <= args.rows <= 30 and args.square_size > 0 and .5 <= args.fps <= 240):
        parser.error("Invalid board geometry or FPS")
    pattern = (args.cols, args.rows)
    board = np.zeros((args.cols * args.rows, 3), dtype=np.float32)
    board[:, :2] = np.mgrid[0:args.cols, 0:args.rows].T.reshape(-1, 2) * args.square_size
    object_points, image_points = [], []
    image_size = None

    def frames():
        if args.input.is_dir():
            paths = sorted(p for p in args.input.iterdir() if p.suffix.lower() in {".jpg", ".jpeg", ".png"})
            for path in paths:
                image = cv2.imread(str(path))
                if image is not None:
                    yield image
        else:
            capture = cv2.VideoCapture(str(args.input))
            if not capture.isOpened():
                raise ValueError("Cannot open calibration input")
            stride = max(1, round(capture.get(cv2.CAP_PROP_FPS) or 30))
            index = 0
            try:
                while True:
                    ok, image = capture.read()
                    if not ok:
                        break
                    if index % stride == 0:
                        yield image
                    index += 1
            finally:
                capture.release()

    for image in frames():
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        size = gray.shape[::-1]
        if image_size and size != image_size:
            raise ValueError("All calibration views must have identical dimensions")
        image_size = size
        ok, corners = cv2.findChessboardCornersSB(gray, pattern, flags=cv2.CALIB_CB_EXHAUSTIVE)
        if ok:
            object_points.append(board.copy())
            image_points.append(corners)
        if len(image_points) >= 80:
            break
    if len(image_points) < 10:
        raise ValueError(f"Only {len(image_points)} usable views. Capture at least 10; 15–30 diverse views are preferred.")
    rms, k, distortion, rotations, translations = cv2.calibrateCamera(object_points, image_points, image_size, None, None)
    errors = []
    for world, observed, r, t in zip(object_points, image_points, rotations, translations):
        projected, _ = cv2.projectPoints(world, r, t, k, distortion)
        errors.append(float(np.sqrt(np.mean(np.sum((observed-projected)**2, axis=2)))))
    coeff = distortion.ravel()
    camera = {"name": "checkerboard calibration", "setup": "monocular", "model": "perspective",
              "fx": float(k[0, 0]), "fy": float(k[1, 1]), "cx": float(k[0, 2]), "cy": float(k[1, 2]),
              **dict(zip(("k1", "k2", "p1", "p2", "k3"), map(float, coeff[:5]))),
              "fps": args.fps, "cols": image_size[0], "rows": image_size[1], "color_order": "BGR"}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(yaml.safe_dump({"Camera": camera}))
    options = {"mode": "calibrated", **{key: camera[key] for key in ("fx", "fy", "cx", "cy", "cols", "rows", "k1", "k2", "p1", "p2", "k3")}}
    args.output.with_suffix(".json").write_text(json.dumps(options, indent=2))
    args.output.with_suffix(".report.json").write_text(json.dumps({"rms_reprojection_pixels": rms,
        "per_view_rms_pixels": errors, "views": len(errors), "square_size": args.square_size,
        "note": "Checkerboard dimensions calibrate the lens; they do not give uploaded SLAM videos metric scale."}, indent=2))
    print(f"Saved {args.output}: {len(errors)} views, RMS reprojection error {rms:.3f} pixels.")


if __name__ == "__main__":
    main()
