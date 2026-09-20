# Backend Service

The backend provides media validation, job orchestration, native SLAM execution, result parsing, artifact delivery, and health/system endpoints. On Lightning AI it runs on port 8000 and remains private behind the frontend `/api` proxy.

## Project-layout requirement

Keep the complete repository structure intact. The folder-local scripts reference shared resources in:

```text
../slam
../scripts
../lightning
```

## Lightning AI installation

Run from the `backend/` directory:

```bash
cd /teamspace/studios/this_studio/Monocular-Sparse-SLAM/backend
BUILD_JOBS=2 bash setup-lightning.sh
```

The script installs system/native dependencies, builds the pinned runner, downloads the ORB vocabulary, and installs Python packages into Lightning's existing Conda environment. It does not create a nested venv or install frontend dependencies.

If compilation exceeds available memory:

```bash
BUILD_JOBS=1 bash setup-lightning.sh
```

Python-only dependency refresh:

```bash
python -m pip install -r requirements-test.txt
```

## Start the API

```bash
ENABLE_SLAM=true bash run-lightning.sh
```

The launcher configures the native runner/vocabulary paths and starts the API on `0.0.0.0:8000`. Keep the terminal running.

## Health verification

From another terminal:

```bash
curl --fail http://127.0.0.1:8000/api/health
curl --fail http://127.0.0.1:8000/api/system
```

Required readiness fields:

```json
{"status":"healthy","slam_runner_available":true,"slam_enabled":true}
```

A successful health request confirms configuration and process readiness; a real video upload is still required to verify reconstruction.

## Primary API endpoints

| Method | Path | Purpose |
|---|---|---|
| GET | `/api/health` | Service and native-engine readiness |
| GET | `/api/system` | Version, limits, revision, and processing configuration |
| POST | `/api/v1/slam/process` | Submit video and optional camera configuration |
| GET | `/api/v1/slam/{job_id}` | Poll job state and retrieve completed result |
| GET | `/api/v1/slam/{job_id}/{artifact}` | Download CSV, PLY, or JSON output |

The complete contract is documented in [../docs/api.md](../docs/api.md). Full Studio deployment instructions are in [../lightning/README.md](../lightning/README.md).

## Common failures

| Error | Action |
|---|---|
| `Could NOT find OpenGL` during CMake | Use the current installer, which includes `libgl1-mesa-dev` |
| Lightning rejects venv creation | Use the current scripts; they target the existing Conda environment |
| Runner or vocabulary unavailable | Rerun backend setup and inspect the first failing command |
| Port 8000 already in use | Stop the existing backend process before restarting |
