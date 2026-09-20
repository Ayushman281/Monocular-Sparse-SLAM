# Lightning AI Deployment Guide

This runbook describes the reproducible deployment of Assignment 2 in a dedicated Lightning AI Studio. It covers native/backend installation, frontend installation, service startup, public exposure, validation, benchmarking, and restart procedures.

## Deployment summary

| Item | Configuration |
|---|---|
| Public application | [Lightning AI frontend](https://5173-01m2wsmqs3pv7fk47mnxtzqdr1.cloudspaces.litng.ai/) |
| Public port | 5173 |
| Backend port | 8000, private within the Studio |
| Frontend runtime | Compiled Vite application with `/api` proxy |
| Backend runtime | FastAPI/Uvicorn plus native stella_vslam runner |
| Python environment | Existing Lightning Conda environment; no nested venv |
| Compute requirement | CPU; GPU is not required |

Assignment 1 and Assignment 2 may use the same numeric ports because they run in separate Studios. Lightning generates a different public hostname for each Studio/port combination.

## Service topology

```text
Public HTTPS URL
  -> frontend on 0.0.0.0:5173
       -> /api proxy to 127.0.0.1:8000
            -> FastAPI backend
                 -> native slam_runner and ORB vocabulary
```

Only port 5173 needs to be public. Keeping port 8000 private avoids a second public origin and eliminates frontend CORS configuration.

## 1. Prerequisites

- A dedicated Lightning Studio for Assignment 2.
- The current GitHub repository or complete source package.
- Python 3.11 or newer in the Studio Conda environment.
- Sufficient memory and disk for native compilation.
- A short monocular RGB video for end-to-end verification.

The Studio should contain the complete project structure because folder-local scripts reference shared files under `slam/`, `scripts/`, and `lightning/`.

## 2. Obtain the source

Clone the repository:

```bash
cd /teamspace/studios/this_studio
git clone https://github.com/Ayushman281/Monocular-Sparse-SLAM.git
cd Monocular-Sparse-SLAM
ls backend frontend slam scripts lightning
```

If a source package is uploaded instead, adjust the path to the extracted directory and confirm that the same folders are present.

## 3. Backend installation and startup

Open the first Studio terminal:

```bash
cd /teamspace/studios/this_studio/Monocular-Sparse-SLAM/backend
BUILD_JOBS=2 bash setup-lightning.sh
ENABLE_SLAM=true bash run-lightning.sh
```

Keep this terminal running. The API listens on `0.0.0.0:8000`.

### Backend setup responsibilities

The setup script:

- installs the C/C++ build toolchain, CMake, Ninja, FFmpeg, OpenCV, Eigen, SuiteSparse, yaml-cpp, SQLite, spdlog, and required OpenGL/GLX development interfaces;
- retrieves the pinned g2o, FBoW, and stella_vslam sources;
- applies the offline-completion patch and builds the native runner;
- downloads the pinned FBoW ORB vocabulary; and
- installs the locked Python application and test dependencies into the active Lightning Conda environment.

Lightning Studios allow one managed environment, so the deployment scripts do not create a nested Python virtual environment. If native compilation exceeds available memory, rerun setup with one build job:

```bash
BUILD_JOBS=1 bash setup-lightning.sh
```

For a Python-only dependency refresh after native installation:

```bash
python -m pip install -r requirements-test.txt
```

## 4. Backend verification

From a second terminal:

```bash
curl --fail http://127.0.0.1:8000/api/health
curl --fail http://127.0.0.1:8000/api/system
```

Required health fields:

```json
{"status":"healthy","slam_runner_available":true,"slam_enabled":true}
```

The deployment is not ready if `status` is `not_ready`, the runner is unavailable, or SLAM is disabled.

## 5. Frontend installation and startup

Use the second terminal:

```bash
cd /teamspace/studios/this_studio/Monocular-Sparse-SLAM/frontend
bash setup-lightning.sh
bash run-lightning.sh
```

Keep this terminal running. The frontend listens on `0.0.0.0:5173` and proxies `/api` to the backend on `127.0.0.1:8000`.

The setup script selects Node.js 22.12 or newer, runs `npm ci`, performs the TypeScript check, and builds the hosted frontend with `npm run build:hosted`. It does not install Python packages or rebuild native SLAM.

Equivalent commands when a compatible Node.js version is already active:

```bash
cd /teamspace/studios/this_studio/Monocular-Sparse-SLAM/frontend
npm ci
npm run build:hosted
bash run-lightning.sh
```

## 6. Deployment verification

Verify the API directly and through the frontend proxy:

```bash
curl --fail http://127.0.0.1:8000/api/health
curl --fail http://127.0.0.1:5173/api/health
```

Both requests must return the healthy response. The second request verifies the complete browser-to-frontend-to-backend route.

## 7. Publish the frontend

In the Studio interface:

1. Open the **Ports** tool.
2. Locate port **5173**.
3. Set port 5173 to **Public** or enable its public-link control.
4. Leave port 8000 private.
5. Open the public URL in a private/incognito browser window.
6. Verify the UI and the public `/api/health` endpoint.

Deployment endpoints:

```text
https://5173-01m2wsmqs3pv7fk47mnxtzqdr1.cloudspaces.litng.ai/
https://5173-01m2wsmqs3pv7fk47mnxtzqdr1.cloudspaces.litng.ai/api/health
```

If the public URL returns HTTP 502, confirm that the Studio is awake, both service terminals are still running, both local health requests pass, and port 5173 remains public. Lightning's [web-app hosting documentation](https://lightning.ai/docs/platform/build/host-web-apps) describes custom-port publication and auto-start behavior.

## 8. End-to-end reconstruction test

Use a 5-10 second video with steady translational motion through a static, textured, well-lit scene. Avoid pure rotation, strong blur, digital zoom, scene cuts, and heavy stabilization.

Browser acceptance steps:

1. Select the video.
2. Use calibrated camera parameters when available; otherwise retain the documented FOV approximation.
3. Start reconstruction.
4. Confirm that the job completes and the viewer displays landmarks and a camera path.
5. Confirm that measured metrics are populated.
6. Download `trajectory.csv`, `pointcloud.ply`, and `result.json`.

Scripted HTTP smoke test:

```bash
cd /teamspace/studios/this_studio/Monocular-Sparse-SLAM
export EXECUTION_TARGET=lightning
export ENABLE_SLAM=true
python scripts/http_smoke.py --video /path/to/test-video.mp4
```

## 9. Performance benchmark

Run at least five repetitions using the same approximately ten-second clip:

```bash
cd /teamspace/studios/this_studio/Monocular-Sparse-SLAM
export EXECUTION_TARGET=lightning
export ENABLE_SLAM=true
python scripts/benchmark.py \
  --video /path/to/approximately-10-second-video.mp4 \
  --runs 5
```

Generated evidence is stored under `benchmarks/runs/<UTC-date>/`. Transfer the accepted environment and result summary to [../benchmarks/benchmark_results.md](../benchmarks/benchmark_results.md). Use `--official` only with a clean committed checkout and an input duration accepted by the benchmark script.

## 10. Restart procedure

Installation artifacts normally persist when the Studio sleeps. Restart the services without repeating setup.

Backend terminal:

```bash
cd /teamspace/studios/this_studio/Monocular-Sparse-SLAM/backend
ENABLE_SLAM=true bash run-lightning.sh
```

Frontend terminal:

```bash
cd /teamspace/studios/this_studio/Monocular-Sparse-SLAM/frontend
bash run-lightning.sh
```

Repeat both local health checks and the public health check. In-progress jobs do not survive a stopped Studio.

## 11. Optional combined workflow

The folder-specific workflow is preferred for troubleshooting. Combined wrappers are also available from the project root:

```bash
cd /teamspace/studios/this_studio/Monocular-Sparse-SLAM
BUILD_JOBS=2 bash lightning/setup.sh
ENABLE_SLAM=true bash lightning/run.sh
```

Do not use the combined launcher while either service is already running.

## Troubleshooting

| Symptom | Resolution |
|---|---|
| `Could NOT find OpenGL` | Use the current setup scripts; `libgl1-mesa-dev` supplies g2o's exported CMake dependency while the viewer remains disabled |
| `Venv creation is not allowed` | Use the current Lightning scripts, which install into the existing Conda environment |
| `Missing script: build:hosted` | Synchronize the current frontend `package.json`, Vite configuration, hosted app config, and deployment scripts |
| Port 8000 or 5173 is occupied | Stop the older Assignment 2 process and restart the service on its documented port |
| Frontend reports engine unavailable | Verify both local health URLs and confirm the backend was started with `ENABLE_SLAM=true` |
| Public URL returns 502 | Wake the Studio, restart both services, verify local health, and confirm public visibility for 5173 |
| Runner or vocabulary is missing | Rerun backend setup and retain the first failing command/output |
| Native compilation is killed | Retry with `BUILD_JOBS=1` or use a Studio with more memory |
| Reconstruction produces few points | Use a sharper clip with stronger texture and translational motion |

## Submission acceptance checklist

- [ ] Direct backend health is healthy.
- [ ] Frontend-proxied health is healthy.
- [ ] Public URL opens from a private browser or separate network.
- [ ] Public `/api/health` is healthy.
- [ ] A real video produces visible landmarks and a trajectory.
- [ ] CSV, PLY, and JSON artifacts download successfully.
- [ ] Five-run timing and Studio machine details are recorded.
- [ ] The Studio will remain available to the evaluator, or restart instructions are supplied.
