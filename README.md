# Assignment 2: Monocular RGB Sparse Point-Cloud SLAM

A web application that estimates camera motion and reconstructs a sparse three-dimensional landmark map from a single RGB video. The system combines a React/Three.js frontend, a FastAPI orchestration service, a native C++17 runner, and the pinned stella_vslam 0.7.0 engine.

## Submission deliverables

| Deliverable | Location |
|---|---|
| Deployed application | [Lightning AI frontend](https://5173-01m2wsmqs3pv7fk47mnxtzqdr1.cloudspaces.litng.ai/) |
| Public health endpoint | [`/api/health`](https://5173-01m2wsmqs3pv7fk47mnxtzqdr1.cloudspaces.litng.ai/api/health) |
| Source repository | [Ayushman281/Monocular-Sparse-SLAM](https://github.com/Ayushman281/Monocular-Sparse-SLAM) |
| Source-code package | `Monocular-Sparse-SLAM-Assignment-2.zip` |
| Lightning AI runbook | [lightning/README.md](lightning/README.md) |
| AWS runbook | [aws/README.md](aws/README.md) |
| Benchmark record | [benchmarks/benchmark_results.md](benchmarks/benchmark_results.md) |
| Third-party inventory | [THIRD_PARTY.md](THIRD_PARTY.md) |

The Lightning URL is tied to the Assignment 2 Studio. If the Studio is sleeping or either service is stopped, the public address may return HTTP 502 until the backend and frontend are restarted. Deployment verification is defined in the [Lightning AI runbook](lightning/README.md#6-deployment-verification).

## Technical overview

### Terminology

- **Monocular:** input is captured by one RGB camera rather than a stereo pair, depth camera, or camera/IMU system.
- **Sparse:** the reconstruction contains selected visual landmarks, not a dense surface, mesh, or photorealistic model.
- **SLAM:** *Simultaneous Localization and Mapping* estimates camera motion while constructing a map of the observed environment.

Monocular sparse SLAM therefore estimates a camera trajectory and sparse 3D landmark map from a single RGB sequence. Absolute metric scale is not observable from monocular vision alone, so all exported coordinates use an unknown but internally consistent global scale.

### Processing pipeline

1. Accept an MP4, MOV, WebM, or AVI upload.
2. Validate the container, codec, duration, frame rate, dimensions, orientation, and pixel aspect ratio with FFprobe.
3. Normalize the video to a bounded constant-frame-rate stream with FFmpeg.
4. Derive camera intrinsics from supplied calibration or a documented horizontal-field-of-view approximation.
5. Run ORB tracking, initialization, triangulation, keyframe mapping, bundle adjustment, place recognition, and loop correction through stella_vslam.
6. Parse and validate the native trajectory and landmark exports.
7. Render the trajectory and sparse point cloud in Three.js and provide downloadable artifacts.

### Outputs

| Output | Description |
|---|---|
| Interactive viewer | Sparse landmarks, camera path, start/end markers, orbit, zoom, pan, and layer controls |
| `trajectory.csv` | Timestamped camera-to-world poses and keyframe flags |
| `pointcloud.ply` | Finite sparse landmarks retained by the observation filter |
| `result.json` | Input metadata, camera parameters, timings, SLAM statistics, warnings, and browser geometry |

## Architecture

```text
Browser
  -> React + TypeScript + Three.js
       -> same-origin /api requests
            -> FastAPI + Uvicorn
                 -> FFprobe/FFmpeg preprocessing
                 -> bounded asynchronous job manager
                 -> C++17 slam_runner
                      -> stella_vslam
                           -> OpenCV + Eigen + g2o + FBoW
```

### Deployment topology

| Environment | Public service | Private service | Routing |
|---|---|---|---|
| Lightning AI | Vite preview server on 5173 | FastAPI on 8000 | Vite proxies `/api` to `127.0.0.1:8000` |
| AWS | Nginx on 80/443 | FastAPI container on 8000 | Nginx proxies `/api` over the Compose network |

The same backend, native runner, and frontend source are used in both environments. Provider-specific behavior is limited to process startup, networking, filesystem paths, and infrastructure configuration.

## Major technical decisions

| Decision | Rationale |
|---|---|
| Pin stella_vslam and native dependencies by commit | Makes the native build and runtime behavior reproducible |
| Keep SLAM in a native C++ process | Preserves the engine's performance characteristics and isolates native failures from the API process |
| Use FastAPI for orchestration | Provides typed validation, bounded uploads, job state, artifact delivery, and health endpoints |
| Use a same-origin `/api` proxy | Avoids provider-specific frontend URLs and unnecessary CORS configuration |
| Limit concurrency to one job by default | Prevents oversubscription on small hosted CPU instances |
| Export corrected final poses and real landmarks | Avoids synthetic geometry and inconsistent pre-/post-loop-closure results |
| Expose relative scale explicitly | Prevents monocular output from being misrepresented as metric reconstruction |
| Retain measurement provenance | Associates benchmark results with the input hash, application revision, environment, and native engine |

Detailed design information is available in [docs/architecture.md](docs/architecture.md), [docs/slam_pipeline.md](docs/slam_pipeline.md), and [docs/api.md](docs/api.md).

## Technology stack and external components

| Layer | Components |
|---|---|
| Frontend | React 19.3.0, React DOM 19.3.0, TypeScript 5.9.3, Vite 8.3.0, Three.js 0.180.0 |
| Backend | Python 3.11+, FastAPI 0.135.1, Uvicorn 0.41.0, Pydantic 2.12.5, NumPy 2.2.6, PyYAML 6.0.3 |
| Native SLAM | C++17, stella_vslam 0.7.0 at `525231147319bcd31242f981078c36d9272727b4` |
| Computer vision | OpenCV, Eigen, g2o, FBoW, SuiteSparse, OpenMP |
| Media processing | FFmpeg and FFprobe |
| Deployment | Lightning AI Studio; Docker Compose and Nginx for AWS |
| Validation | pytest, HTTPX, shell syntax checks, HTTP smoke tests, and repeated benchmark tooling |

No neural-network model is used. The downloaded FBoW ORB vocabulary is fixed place-recognition data, not a neural model. Exact source revisions, roles, and license notices are listed in [THIRD_PARTY.md](THIRD_PARTY.md).

## Repository layout

```text
backend/      FastAPI application, tests, Dockerfile, and Lightning entry points
frontend/     React/Three.js application, Nginx configuration, and hosted build scripts
slam/         Native runner, dependency pins, and offline-completion patch
scripts/      Build, vocabulary, calibration, validation, smoke-test, and benchmark tools
lightning/    Lightning AI deployment runbook and shared launch scripts
aws/          AWS EC2 and Docker Compose deployment runbook
docs/         Architecture, API, requirements, limitations, and validation records
benchmarks/   Benchmark report and generated-run destination
```

## Deployment quick start

### Lightning AI

Backend terminal:

```bash
cd /teamspace/studios/this_studio/monocular-sparse-slam-source/monocular-sparse-slam/backend
BUILD_JOBS=2 bash setup-lightning.sh
ENABLE_SLAM=true bash run-lightning.sh
```

Frontend terminal:

```bash
cd /teamspace/studios/this_studio/monocular-sparse-slam-source/monocular-sparse-slam/frontend
bash setup-lightning.sh
bash run-lightning.sh
```

Expose frontend port 5173 through the Lightning Ports tool. Backend port 8000 can remain private because `/api` is proxied through the frontend. See [lightning/README.md](lightning/README.md) for the complete setup, restart, verification, and troubleshooting procedure.

### AWS

The AWS deployment uses Docker Compose on an Ubuntu EC2 instance. Nginx exposes the frontend and `/api`, while the backend remains on the private Compose network. See [aws/README.md](aws/README.md) for infrastructure, security-group, installation, verification, TLS, and operations guidance.

## Input guidance

Recommended input is a 5-10 second video of a mostly static, textured, well-lit environment. Camera motion should be slow and include translation, such as a short sideways movement or walk through a room. Avoid pure rotation, motion blur, digital zoom, scene cuts, strong stabilization, rapidly moving subjects, and severe rolling shutter.

Use calibrated intrinsics when available. Otherwise, the default 65-degree horizontal field-of-view estimate is accepted with an accuracy warning.

## Performance evaluation

Each successful job reports server processing time, native SLAM time, and real-time factor. The repeated benchmark additionally records result-ready time, input hash, source revision, host information, tracking coverage, keyframes, map points, and loop edges.

### Recorded Lightning toolchain

| Item | Value observed in installation logs |
|---|---|
| Platform | Lightning AI Studio |
| Python | 3.12, Studio `cloudspace` Conda environment |
| Node.js / npm | 22.14.0 / 10.9.2 |
| CMake | 3.28 |
| OpenCV | 4.6.0 |
| OpenMP | 4.5 |
| spdlog | 1.12.0 |
| Native engine | stella_vslam 0.7.0, pinned commit listed above |
| Studio machine / CPU / RAM | Pending benchmark capture |
| Five-run processing result | Pending benchmark capture |

Benchmark command:

```bash
cd /teamspace/studios/this_studio/monocular-sparse-slam-source/monocular-sparse-slam
export EXECUTION_TARGET=lightning
export ENABLE_SLAM=true
python scripts/benchmark.py \
  --video /path/to/approximately-10-second-video.mp4 \
  --runs 5
```

No performance threshold is considered verified until the repeated results and machine details are recorded in [benchmarks/benchmark_results.md](benchmarks/benchmark_results.md). Timing boundaries and acceptance rules are defined in [docs/performance.md](docs/performance.md).

## Known limitations and future work

- Absolute metric scale cannot be recovered from monocular RGB input alone.
- The result is a sparse landmark map, not a dense reconstruction or mesh.
- Accuracy depends on camera calibration, texture, lighting, motion blur, baseline, rolling shutter, and scene dynamics.
- Pure rotation and negligible translation provide insufficient triangulation baseline.
- Only one reconstruction job runs at a time by default.
- Jobs and artifacts are stored locally and do not survive all host restarts.
- Fisheye, stereo, RGB-D, and visual-inertial input are outside the current scope.
- A production deployment should add authentication, rate limiting, durable object storage, a persistent job queue, monitoring, automated TLS, and CI/CD.
- Additional work could include dense reconstruction, known-scale alignment, broader camera models, ATE/RPE evaluation, and automated deployment acceptance tests.

See [docs/limitations.md](docs/limitations.md) for additional detail.

## AI Usage

I used ChatGPT with the **Astra 6** and **GPT 5.6 Sol** language models. Approximately **80% of the assignment code was AI-generated or AI-assisted**. AI support included requirements analysis, architecture proposals, native integration, FastAPI and React implementation, tests, deployment scripts, troubleshooting, and documentation.

I reviewed and modified the implementation, ran the Lightning installation, interpreted native-build and hosting logs, changed backend hosting code and scripts, separated backend/frontend setup, and configured the two-service deployment. Significant recommendations were evaluated rather than accepted automatically. For example, I removed nested virtual-environment creation after Lightning rejected it, added the missing OpenGL development dependency from an observed CMake error, and rejected synthetic geometry or unverified performance claims.

I understand the submitted architecture and accept responsibility for the code and deployment. The full disclosure is available in [AI_USAGE.md](AI_USAGE.md).

## License

Original project code is licensed under the [MIT License](LICENSE). Third-party software and the ORB vocabulary retain their respective licenses and notices.
