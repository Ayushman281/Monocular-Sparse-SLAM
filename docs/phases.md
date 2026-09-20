# Phase ledger

This ledger records goals, reasons, source files, exact next commands, acceptance outcomes, common problems and review concepts. **Source prepared** does not mean **runtime accepted**. Local execution restrictions supersede the master prompt's generic local-testing sequence: native/backend checks run on selected hosted Linux; Docker/public acceptance runs on AWS.

Common Lightning setup commands, from project root:

```bash
bash lightning/setup.sh
ENABLE_SLAM=true bash lightning/run.sh
```

| Phase | Goal and why | Files created | Verification command / expected result | Common problems and review notes | Status |
|---|---|---|---|---|---|
| 0 | Convert requirements and explain geometry before coding | docs/requirements.md, architecture.md, slam_pipeline.md, prerequisites.md | Read checklist; inspect tool versions | Scale cannot come from RGB alone; tool presence is not runtime validation | Documented; prerequisites inspected |
| 1 | Separate Assignment 2 and initialize source history | .gitignore, .gitattributes, README.md, independent .git | `git status --short`; source separate from Assignment 1 | Ignore binaries, uploads, credentials and cache | Initialized |
| 2 | Integrate pinned native engine and dependencies | slam/dependencies.env, CMakeLists.txt, scripts/build_native.sh | `bash scripts/build_native.sh`; Release executable produced | g2o/CMake/linker compatibility and compile memory; never downgrade silently | Source prepared; build pending |
| 3 | Prove real standalone reconstruction | scripts/run_video.py, slam/src/main.cpp | `python scripts/run_video.py --video samples/benchmark.mp4 --output artifacts/poc-01`; actual map | Need parallax/texture and matching calibration | Pending runtime |
| 4 | Calibrate real intrinsics and implement explicit fallback | scripts/calibrate_camera.py, backend/app/camera.py | Calibration command in README; review RMS and geometry tests | Corner vs square counts; resize principal point correctly | Source prepared |
| 5 | Feed decoded frames without playback delay | backend/app/video.py, slam/src/main.cpp | Same standalone command; frame counts agree with duration/FPS | VFR, rotation, corrupt media; CFR timestamps documented | Source prepared |
| 6 | Export corrected camera poses | main.cpp, backend/app/results.py | Inspect artifacts/poc-01/trajectory.csv; transform tests | Twc vs Tcw; gap preservation | Source prepared |
| 7 | Export actual sparse landmarks | main.cpp, results.py | Inspect PLY header/count and geometry | Weak/nonfinite points; arbitrary scale | Source prepared |
| 8 | Preserve drift-reduction mechanisms and finish correction | camera.py, slam/patches/offline-drain.patch | Run real revisit clip and inspect graph loop edges | A revisit may not pass verification; thread-drain lifecycle needs testing | Source prepared |
| 9 | Optimize measured bottlenecks | scripts/benchmark.py, docs/performance.md | Repeated profiling runs; maintain tracking quality | No timings yet; optimize only from evidence | Pending baseline |
| 10 | Orchestrate safe jobs over HTTP | backend/app/main.py, jobs.py, process.py, lightning/run-backend.sh | `ENABLE_SLAM=true bash lightning/run.sh`; ports 8000/5173 start and proxied health is ready | One worker, bounded uploads/jobs, no public stack traces | Source prepared |
| 11 | Upload workflow and calibration controls | frontend/src/App.tsx | `npm.cmd run dev -- --port 5174`; controls render | Preview intentionally disables processing | Preview inspected |
| 12 | Interactive map and trajectory | frontend/src/Viewer.tsx | Inspect actual output in WebGL | Both geometries need the same display rotation | Empty-state preview inspected; actual map pending |
| 13 | Integrate upload through export | scripts/http_smoke.py | `python scripts/http_smoke.py --video samples/benchmark.mp4`; success/downloads | Same-origin routing and native linker path | Pending runtime |
| 14 | Handle corrupt/tracking/timeout/busy failures | backend errors/jobs/main/process, frontend error UI | HTTP smoke plus native timeout tests | Algorithm failure is a failed job, not fabricated success | Source prepared |
| 15 | Exercise geometry/media/lifecycle checks | backend/tests/ | `bash scripts/hosted_validate.sh`; tests and frontend build pass | Fixtures are test-only; no production fallback | Tests written, not run |
| 16 | Demonstrate <=10 seconds | benchmark.py, benchmarks/benchmark_results.md | `python scripts/benchmark.py --video samples/benchmark.mp4 --runs 5 --official` | Clean matching server revision, all runs/failed trials retained | Unverified |
| 17 | Package dependencies and reverse proxy | backend/Dockerfile, frontend/Dockerfile, docker-compose.yml, frontend/vite.config.ts | Lightning `/api` proxy check; `APP_REVISION="$(git rev-parse HEAD)" docker compose build` on AWS | Distro/link/runtime libraries; actual build required | Source prepared |
| 18 | Production-style test in authorized host | docs/aws-deployment.md | `docker compose up -d`; health/UI/upload | Container CPU/RAM/tmpfs limits affect performance | Pending AWS |
| 19 | Prepare reviewer-facing documentation | README, docs/, AI_USAGE, THIRD_PARTY | Read paths, claims and recipes against source | Do not describe pending recipes as tested deployment | Prepared |
| 20 | Pre-public functional acceptance | docs/acceptance.md, validation.md | Repeat hosted real-video and failure checks | Source review cannot sign off runtime | Pending |
| 21 | Select AWS CPU from measurements | docs/aws-deployment.md | Verify region, live pricing, quota/credits and benchmark need | No instance selected or cost claim yet | Deferred |
| 22 | Create approved server | Deployment ledger | Follow verified console plan after cost/access gate | Requires account access/billing approval | Deferred |
| 23 | Configure server and restricted access | AWS runbook | Install Docker, clone revision, configure .env | Secrets outside repo, SSH restricted | Deferred |
| 24 | Deploy containers | Compose/Dockerfiles | `docker compose up -d`; healthy services | Avoid exposing backend port | Deferred |
| 25 | Verify public Nginx routing | frontend/nginx.conf | Open real URL from independent network; test upload | HTTPS/domain configuration if available | Deferred |
| 26 | Benchmark actual AWS deployment | benchmark.py/report | Same official benchmark with `--url http://127.0.0.1` | Docker limits and host load recorded | Deferred |
| 27 | Verify submission completeness | docs/acceptance.md, README | All mandatory evidence checked, source package matches | No public URL or performance fabrication | Deferred |
| 28 | Explain and modify the implementation | docs/technical_review.md | Trace a real result and perform exercises | Understand underlying geometry, not only UI | Study guide prepared; hands-on review pending |

After each hosted phase, append commands, actual output/log paths, failures/fixes and environment to validation.md. After final measurements, replace pending report cells with reproducible evidence, not example numbers.
