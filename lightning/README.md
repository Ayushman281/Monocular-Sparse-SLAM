# Deploy Assignment 2 on Lightning AI

I used this process to install, start, verify, and publish both the backend and frontend in a dedicated Lightning AI Studio. I have written it so that I—or an evaluator—can reproduce the deployment systematically.

**Recorded deployment URL:** [https://5173-01m2wsmqs3pv7fk47mnxtzqdr1.cloudspaces.litng.ai/](https://5173-01m2wsmqs3pv7fk47mnxtzqdr1.cloudspaces.litng.ai/)

Assignment 2 can use backend port **8000** and frontend port **5173** even if Assignment 1 uses the same port numbers. Each project is hosted in a different Studio, and Lightning generates different URLs for the Studio/port combination.

## 1. Prerequisites

- A separate Lightning Studio for Assignment 2.
- The complete current source tree—not only the older embedded Git bundle.
- Python 3.11+ in the Studio's default Conda environment.
- Enough memory and disk space to compile the native dependencies.
- A short RGB test video for final end-to-end verification.

My project is CPU-based, so I do not require a GPU. I review Studio credits, machine selection, persistence, auto-stop, and auto-start settings before leaving a service running.

## 2. Confirm the project location

Upload/extract the source or clone the current repository. Enter the directory containing `backend/`, `frontend/`, `slam/`, `scripts/`, and `lightning/`:

```bash
cd /teamspace/studios/this_studio/monocular-sparse-slam-source/monocular-sparse-slam
pwd
ls backend frontend slam scripts lightning
```

Do not run Assignment 2 commands from the Assignment 1 directory.

## 3. Install and start the backend

Open the first Studio terminal:

```bash
cd /teamspace/studios/this_studio/monocular-sparse-slam-source/monocular-sparse-slam/backend
BUILD_JOBS=2 bash setup-lightning.sh
ENABLE_SLAM=true bash run-lightning.sh
```

Keep this terminal running. The API listens on `0.0.0.0:8000`.

Backend setup performs the following work:

- installs the Ubuntu/Debian compiler, CMake, Ninja, FFmpeg, OpenCV, Eigen, SuiteSparse, yaml-cpp, SQLite, spdlog, and OpenGL/GLX development interface required by g2o's exported CMake package;
- downloads pinned g2o, FBoW, and stella_vslam sources;
- applies the documented offline-completion patch and builds the native runner;
- downloads the pinned FBoW ORB vocabulary; and
- installs the locked Python application/test requirements into Lightning's existing Conda environment.

Lightning Studios permit one environment, so these scripts intentionally do **not** create a nested Python virtual environment. If native compilation runs out of memory, rerun setup with `BUILD_JOBS=1`.

For a later Python-only dependency refresh, run this from `backend/`:

```bash
python -m pip install -r requirements-test.txt
```

## 4. Check the backend locally

Open a second terminal while the backend remains running:

```bash
curl --fail http://127.0.0.1:8000/api/health
curl --fail http://127.0.0.1:8000/api/system
```

The important health fields are:

```json
{"status":"healthy","slam_runner_available":true,"slam_enabled":true}
```

`status: not_ready`, `slam_runner_available: false`, or `slam_enabled: false` means the application must not be submitted as ready.

## 5. Install and start the frontend

Use the second terminal:

```bash
cd /teamspace/studios/this_studio/monocular-sparse-slam-source/monocular-sparse-slam/frontend
bash setup-lightning.sh
bash run-lightning.sh
```

Keep this terminal running. The compiled frontend listens on `0.0.0.0:5173` and proxies relative `/api` requests to `127.0.0.1:8000`.

Frontend setup selects Node 22.12 or newer, runs `npm ci`, checks TypeScript, and creates the hosted production build with `npm run build:hosted`. It does not install Python or compile native SLAM.

If Node is already suitable, the equivalent folder-local commands are:

```bash
cd /teamspace/studios/this_studio/monocular-sparse-slam-source/monocular-sparse-slam/frontend
npm ci
npm run build:hosted
bash run-lightning.sh
```

## 6. Verify the deployment

From a third terminal, verify the backend directly and through the frontend proxy:

```bash
curl --fail http://127.0.0.1:8000/api/health
curl --fail http://127.0.0.1:5173/api/health
```

Both commands must return a healthy engine. The second proves that the same-origin frontend proxy can reach the private backend.

Then open the Studio **Ports** tool:

1. Locate port **5173**.
2. Set its visibility to **Public** or use the public-link control.
3. Keep port **8000** private; the public frontend already proxies `/api`.
4. Open the generated 5173 URL in an incognito/private browser window.
5. Verify both the UI and `<PUBLIC_FRONTEND_URL>/api/health`.

For this deployment, check:

```text
https://5173-01m2wsmqs3pv7fk47mnxtzqdr1.cloudspaces.litng.ai/
https://5173-01m2wsmqs3pv7fk47mnxtzqdr1.cloudspaces.litng.ai/api/health
```

An automated external check made while preparing this documentation received HTTP 502. If that continues, confirm that the Studio is awake, both terminals/processes are running, the two local curl commands pass, and port 5173 is public. A 502 is not a healthy submission result.

Lightning's official [web-app hosting guide](https://lightning.ai/docs/platform/build/host-web-apps) confirms that custom apps can be shared through the Ports tool. Auto-start can reduce idle cost but introduces a cold-start delay.

## 7. Test a real reconstruction

Use a 5–10 second video with:

- steady, slow movement;
- sideways or forward translation, not only rotation;
- a static, textured, well-lit scene; and
- no digital zoom, scene cuts, or heavy stabilization.

In the browser:

1. Choose the video.
2. Leave **Approximate from field of view** selected if no calibration is available; 65° is the default estimate.
3. Select **Run reconstruction**.
4. Confirm that the job succeeds, landmarks and the path appear, measured metrics are populated, and all downloads work.

For a scripted HTTP smoke test:

```bash
cd /teamspace/studios/this_studio/monocular-sparse-slam-source/monocular-sparse-slam
export EXECUTION_TARGET=lightning
export ENABLE_SLAM=true
python scripts/http_smoke.py --video /path/to/test-video.mp4
```

## 8. Measure processing time

Run at least five repetitions on the same approximately ten-second clip:

```bash
cd /teamspace/studios/this_studio/monocular-sparse-slam-source/monocular-sparse-slam
export EXECUTION_TARGET=lightning
export ENABLE_SLAM=true
python scripts/benchmark.py \
  --video /path/to/approximately-10-second-video.mp4 \
  --runs 5
```

The script writes raw results and environment details under `benchmarks/runs/<UTC-date>/`. Copy the accepted environment and timing summary into `benchmarks/benchmark_results.md`. Use `--official` only from a clean committed checkout with an input duration accepted by the script.

## 9. Restart after the Studio sleeps

Installation usually persists, so start the services again without repeating setup.

Backend terminal:

```bash
cd /teamspace/studios/this_studio/monocular-sparse-slam-source/monocular-sparse-slam/backend
ENABLE_SLAM=true bash run-lightning.sh
```

Frontend terminal:

```bash
cd /teamspace/studios/this_studio/monocular-sparse-slam-source/monocular-sparse-slam/frontend
bash run-lightning.sh
```

Repeat the local and public health checks. In-progress jobs do not survive a stopped Studio.

## 10. Optional combined launcher

The folder-specific workflow above is recommended because it makes failures easier to identify. The project also provides combined wrappers from the project root:

```bash
cd /teamspace/studios/this_studio/monocular-sparse-slam-source/monocular-sparse-slam
BUILD_JOBS=2 bash lightning/setup.sh
ENABLE_SLAM=true bash lightning/run.sh
```

Do not use the combined launcher while either service is already running.

## Troubleshooting

- **`Could NOT find OpenGL`:** use the current project files and rerun backend setup. `libgl1-mesa-dev` is included for g2o's CMake dependency; it does not enable the graphical viewer.
- **`Venv creation is not allowed`:** use the current scripts. They install Python packages into Lightning's existing Conda environment and never call `python -m venv`.
- **`Missing script: build:hosted`:** synchronize the current `frontend/package.json`, `frontend/vite.config.ts`, `frontend/public-hosted/app-config.json`, and Lightning scripts. The old source bundle does not contain later hosting changes.
- **Port 8000 or 5173 already in use:** stop the older Assignment 2 process and rerun the service on its documented port.
- **Frontend opens but says the engine is unavailable:** run both local curl commands, check that the backend was started with `ENABLE_SLAM=true`, and inspect the backend terminal.
- **Public URL returns 502:** wake the Studio, restart both services, verify local health, and confirm port 5173 visibility.
- **Runner or vocabulary missing:** rerun `BUILD_JOBS=2 bash setup-lightning.sh` from `backend/` and keep the first failing command/output.
- **Native build is killed:** retry with `BUILD_JOBS=1`; if it still fails, use a Studio with more memory.
- **Reconstruction fails or creates few points:** try a shorter, sharper clip with more texture and translational camera motion; camera input quality is often the cause.

## Final Lightning submission checklist

- [ ] Backend direct health is healthy.
- [ ] Frontend-proxied health is healthy.
- [ ] Public 5173 URL opens from an incognito browser or another network.
- [ ] Public `/api/health` is healthy.
- [ ] A real video reconstruction completes and produces visible geometry.
- [ ] CSV, PLY, and JSON downloads work.
- [ ] Five-run processing measurements and Studio machine details are recorded.
- [ ] The Studio remains available for the evaluator or restart instructions are provided.
