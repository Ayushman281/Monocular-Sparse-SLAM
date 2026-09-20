# Assignment 2 — Monocular RGB Sparse Point-Cloud SLAM

I built this application to estimate a camera's motion and reconstruct a sparse three-dimensional map from a single RGB video. I combined a React/Three.js interface, a FastAPI service, a C++ runner, and the pinned stella_vslam 0.7.0 engine.

## Submission links

| Deliverable | Location |
|---|---|
| Public Lightning AI application | [Open the deployed frontend](https://5173-01m2wsmqs3pv7fk47mnxtzqdr1.cloudspaces.litng.ai/) |
| Public health check | [Open `/api/health`](https://5173-01m2wsmqs3pv7fk47mnxtzqdr1.cloudspaces.litng.ai/api/health) |
| GitHub source repository | [Ayushman281/Monocular-Sparse-SLAM](https://github.com/Ayushman281/Monocular-Sparse-SLAM) |
| Downloadable source package | `monocular-sparse-slam-assignment-2.zip` |
| Lightning AI deployment guide | [lightning/README.md](lightning/README.md) |
| AWS deployment guide | [aws/README.md](aws/README.md) |
| API reference | [docs/api.md](docs/api.md) |
| Third-party components | [THIRD_PARTY.md](THIRD_PARTY.md) |

The URL above is the deployment address supplied by the project operator. Lightning Studios may sleep or stop. At the time of this documentation update, an external automated request received HTTP 502, so the Studio must be restarted and the two health checks in the [Lightning guide](lightning/README.md#6-verify-the-deployment) must pass before submission.

## Terminology

- **Monocular** means that the system receives images from one camera, rather than stereo cameras or a depth sensor.
- **Sparse** means that it reconstructs selected visual landmarks—typically distinctive corners and textured features—not a dense surface or photorealistic model.
- **SLAM** means *Simultaneous Localization and Mapping*: the system estimates where the camera moved while building a map of the observed environment.

Together, **monocular sparse SLAM** means estimating a single camera's trajectory and a sparse 3D landmark map from ordinary RGB video. Because one camera does not provide an absolute distance reference, the result has an unknown global scale. Coordinates are relative, not metres.

## What the application does

1. Accepts an MP4, MOV, WebM, or AVI video (up to 200 MB and 30 seconds by default).
2. Validates the media, corrects orientation, normalizes frame rate, and limits the longest frame dimension to 640 pixels.
3. Uses camera calibration when I provide it, or estimates intrinsics from a stated horizontal field of view.
4. Runs ORB feature tracking, keyframe mapping, triangulation, bundle adjustment, place recognition, and loop correction through stella_vslam.
5. Displays the recovered sparse landmarks and camera trajectory in an interactive Three.js viewer.
6. Reports real server timing, tracked frames, keyframes, landmarks, and loop edges.
7. Exports `trajectory.csv`, `pointcloud.ply`, and `result.json`.

The intended input is a short, steady video of a mostly static, well-lit, textured scene with deliberate sideways/forward camera translation. Pure rotation, heavy blur, digital zoom, scene cuts, and moving crowds are poor inputs because they provide unreliable geometry.

## Architecture

```text
Browser
  └─ React + TypeScript + Three.js (public port 5173 on Lightning)
       └─ relative /api requests
            └─ FastAPI + Uvicorn (private port 8000)
                 ├─ FFprobe/FFmpeg validation and normalization
                 ├─ bounded job manager and temporary storage
                 └─ C++17 slam_runner
                      └─ stella_vslam + OpenCV + Eigen + g2o + FBoW
                           └─ trajectory, sparse landmarks, metrics
```

On Lightning AI, Vite serves the compiled frontend on port 5173 and proxies `/api` to the backend on port 8000. Only port 5173 needs to be public. On AWS, Nginx serves the frontend on ports 80/443 and proxies `/api` to an internal backend container; port 8000 is not published.

### Major technical decisions

| Decision | Reason |
|---|---|
| stella_vslam 0.7.0 pinned by commit | Reproducible, CPU-capable, feature-based sparse SLAM with mapping and loop correction |
| Native C++ engine behind a Python API | Keeps performance-critical vision code native while FastAPI handles validation, jobs, and HTTP |
| Same-origin `/api` proxy | Avoids hard-coded provider hostnames and unnecessary CORS configuration |
| One active reconstruction by default | Prevents CPU and memory oversubscription on small hosted machines |
| Real geometry only | The UI never substitutes fabricated points, trajectories, loop events, or benchmark values |
| Relative-scale output | Correctly communicates the fundamental scale ambiguity of monocular vision |
| Pinned native sources and vocabulary | Makes native builds and place-recognition data traceable |

More detail is available in [docs/architecture.md](docs/architecture.md) and [docs/slam_pipeline.md](docs/slam_pipeline.md).

## Libraries, frameworks, and external components

| Layer | Components |
|---|---|
| Frontend | React 19.3.0, React DOM 19.3.0, TypeScript 5.9.3, Vite 8.3.0, Three.js 0.180.0 |
| Backend | Python 3.11+, FastAPI 0.135.1, Uvicorn 0.41.0, Pydantic 2.12.5, NumPy 2.2.6, PyYAML 6.0.3 |
| Native SLAM | C++17, stella_vslam 0.7.0 at commit `525231147319bcd31242f981078c36d9272727b4` |
| Vision and optimization | OpenCV, Eigen, g2o, FBoW, SuiteSparse, OpenMP |
| Media | FFmpeg and FFprobe |
| AWS edge | Docker Compose and Nginx |
| Tests and measurement | pytest, HTTPX, and the repository benchmark/smoke scripts |

There is **no neural-network pretrained model** in this project. The downloaded FBoW ORB vocabulary is fixed pretrained place-recognition data, not a learned neural model. Exact native revisions, licenses, and notices are recorded in [THIRD_PARTY.md](THIRD_PARTY.md).

## Repository structure

```text
backend/      FastAPI application, tests, Dockerfile, Lightning scripts
frontend/     React/Three.js application, Nginx config, Lightning scripts
slam/         Native C++ runner, dependency pins, stella completion patch
scripts/      Native build, vocabulary, smoke, calibration, and benchmark tools
lightning/    Lightning AI deployment runbook and shared launch helpers
aws/          AWS EC2/Docker deployment runbook
docs/         Architecture, API, performance, limitations, and validation records
benchmarks/   Benchmark report template and generated-run destination
```

## Run on Lightning AI

Use a dedicated Assignment 2 Studio. Backend and frontend setup intentionally start from their own folders.

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

Then expose port **5173** using Lightning's Ports tool. Do not expose 8000 unless a separate public API endpoint is specifically required. Full first-time installation, restart, health-check, troubleshooting, and benchmarking instructions are in [lightning/README.md](lightning/README.md).

## Run on AWS

The AWS design uses one Ubuntu EC2 host and Docker Compose:

- Nginx/frontend is public on 80 (and 443 after TLS configuration).
- FastAPI and the native SLAM runner remain on the private Compose network.
- Source and native dependencies are built into the images.

Follow [aws/README.md](aws/README.md) for EC2 creation, Docker installation, security-group rules, deployment, verification, logs, HTTPS, updates, and cleanup.

## Processing time and test environment

The application displays the measured processing time for every successful job. The repeated benchmark records server time, observed result-ready time, SLAM time, real-time factor, map size, tracking coverage, input hash, source revision, and host information.

Known Lightning environment details from the supplied installation logs:

| Item | Recorded value |
|---|---|
| Platform | Lightning AI Studio |
| Python | 3.12, Studio `cloudspace` Conda environment |
| Node.js / npm | 22.14.0 / 10.9.2 |
| CMake | 3.28 |
| OpenCV | 4.6.0 |
| OpenMP | 4.5 |
| spdlog | 1.12.0 |
| Native engine | stella_vslam 0.7.0, pinned commit shown above |
| CPU / vCPU / RAM / Studio machine | Not supplied |
| Five-run measured processing time | **Not supplied; must be recorded from an actual benchmark** |

Run this on the same Lightning Studio while the backend is running:

```bash
cd /teamspace/studios/this_studio/monocular-sparse-slam-source/monocular-sparse-slam
export EXECUTION_TARGET=lightning
export ENABLE_SLAM=true
python scripts/benchmark.py --video /path/to/approximately-10-second-video.mp4 --runs 5
```

Copy the generated summary into [benchmarks/benchmark_results.md](benchmarks/benchmark_results.md) before final submission. Do not claim the ten-second target unless every required run actually passes. The timing definitions and acceptance criteria are in [docs/performance.md](docs/performance.md).

## Known limitations and future improvements

- Absolute metric scale cannot be recovered from unassisted monocular RGB video.
- The output is a sparse landmark cloud, not a dense mesh, depth map, or photorealistic reconstruction.
- Performance depends strongly on texture, lighting, motion blur, camera translation, rolling shutter, dynamic objects, and calibration quality.
- Pure rotation or very small translation provides insufficient triangulation baseline.
- Only one job runs at a time by default; jobs and results are stored locally and are not durable across restarts.
- Fisheye, stereo, RGB-D, and visual-inertial inputs are outside the current scope.
- Lightning Studio links can be unavailable while the Studio sleeps or its processes are stopped.
- The deployment would benefit from durable object storage, a persistent job queue, authentication, rate limiting, HTTPS/domain automation, monitoring, CI/CD, and benchmark-driven instance sizing.
- With more time, I would add dense reconstruction, optional known-scale alignment, broader camera models, dataset-based trajectory evaluation (ATE/RPE), and automated deployment tests.

See [docs/limitations.md](docs/limitations.md) for the extended engineering discussion.

## AI Usage

ChatGPT was used with the **Astra 6** and **GPT 5.6 Sol** language models. Approximately **80% of the assignment code was AI-generated or AI-assisted**. AI was used for requirements decomposition, architecture, the native C++/stella_vslam integration, FastAPI and React implementation, tests, deployment scripts, troubleshooting, and documentation.

I reviewed the project, made deployment decisions, ran the Lightning installation, interpreted build/runtime logs, modified backend hosting code and scripts, configured the services and ports, and developed a good understanding of the complete data flow and major limitations. I did not accept AI recommendations blindly: I removed the nested virtual-environment approach after Lightning rejected it, added the OpenGL development dependency after a real CMake failure, separated frontend and backend setup into their own folders, and rejected claims that lacked runtime evidence.

I accept responsibility for the submitted code and can explain its architecture and behavior. My complete disclosure is in [AI_USAGE.md](AI_USAGE.md).

## License

Original project code is licensed under the [MIT License](LICENSE). Third-party libraries, native dependencies, and the ORB vocabulary retain their respective licenses and notices.
