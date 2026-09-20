# HTTP and native contracts

The backend is a single Uvicorn worker and is disabled without the explicit hosted target and SLAM opt-in. All paths below are relative to the app origin.

| Method / path | Contract |
|---|---|
| GET `/api/health` | Liveness and installed runner/vocabulary availability; no expensive SLAM work |
| GET `/api/system` | Engine/version, application revision, safe limits and processing mode |
| POST `/api/v1/slam/process` | One multipart `video` file and optional `camera` JSON string; returns 202 with `job_id` and `status_url` |
| GET `/api/v1/slam/{job_id}` | `status`, honest `stage`, optional error/code and completed result |
| GET `/api/v1/slam/{job_id}/trajectory.csv` | Final `Twc` timestamp, translation, quaternion, keyframe flag |
| GET `/api/v1/slam/{job_id}/pointcloud.ply` | Complete finite map landmarks retained by observation filter |
| GET `/api/v1/slam/{job_id}/result.json` | Result with original/processing metadata, camera parameters, timings and display geometry |

Approximate camera JSON: `{"mode":"approximate","horizontal_fov":65}`. Calibrated JSON requires `mode`, `fx,fy,cx,cy,cols,rows`; distortion coefficients default to zero. Dimensions describe the upright original input. Optional `target_fps` is validated and capped at the server's configured rate and source FPS. The script-generated calibration `.json` has this exact shape.

Typical request:

```bash
curl --fail -F 'video=@samples/benchmark.mp4' \
  -F 'camera={"mode":"approximate","horizontal_fov":65}' \
  http://127.0.0.1:8000/api/v1/slam/process
```

Use the actual returned job ID for status/download calls. HTTP 413 covers oversized bodies/files, 422 invalid settings/empty files, 429 busy admission, 503 missing native components, 507 insufficient temporary space. Metadata/algorithm failures after acceptance produce a terminal failed job with a useful error code; they do not replace geometry with test doubles.

Result trajectory rows are `[timestamp,tx,ty,tz,qx,qy,qz,qw]`. Points are `[x,y,z]`. `slam` carries actual frame, keyframe, point and graph-loop-edge counts, final optimization status, engine revision and internal timings. `processing` carries measured native-process and total server time plus RTF. `target_met` is a per-run timing indicator; only the official repeated benchmark and functional/public acceptance establish completion.

## Native boundary

```bash
slam_runner --video normalized.mkv --config camera.yaml \
  --vocab orb_vocab.fbow --output new-result-directory --no-viewer
```

`--drain-timeout` defaults to 30 seconds; `--version` reports the pinned engine and patch. Exit 0 means the source's minimum geometry checks passed, 2 means insufficient stable reconstruction, and 1 means a native/input/config/optimization failure. The backend still validates all exports. The runner requires normalized CFR input exactly matching the camera dimensions; `scripts/run_video.py` prepares arbitrary uploads through the same services as HTTP. It creates no display window and has no playback sleep.
