# Validation record

## 2026-09-19 — source and frontend preview only

Environment: Windows development PC, Node v22.15.0/npm 10.9.2, Python 3.12.10, Git 2.49.0.windows.1, WSL 2.5.7.0 installed. Backend execution and builds are prohibited here by the workspace policy. Assignment 1 source was left untouched; Assignment 2 was created in an independent nested repository.

Completed observations:

- Read the full assignment and parent policy; inspected existing source structure and Git state.
- Queried upstream Git refs and inspected the pinned stella_vslam 0.7.0 source headers/implementations for feed, export, mapping queues, loop BA, feature parameters and graph APIs.
- Prepared an offline completion patch; inspected source diff and reverse patch compatibility. This does not prove native compilation or concurrency correctness.
- Verified direct Python package version metadata on PyPI; did not install or execute the backend locally.
- Ran `npm.cmd install --ignore-scripts --no-audit --no-fund` in frontend, producing package-lock.json.
- Ran `npm.cmd run dev -- --port 5174` on loopback.
- Browser verified the title, empty reconstruction viewer, disabled reconstruction in preview, scale warning, expanded advanced settings and calibrated fields.
- Inspected desktop screenshot and a 390 px mobile viewport; mobile DOM reported client width=scroll width=375 px (no horizontal overflow). Restored the default viewport.
- Browser diagnostic query returned no warning/error entries during those checks.
- Prepared source, dependency/license notices, hosted recipes and technical review guide. Application-source whitespace inspection passed; patch context lines and verbatim upstream license whitespace are intentionally preserved.

No actual video has been selected or processed. No points, trajectories, benchmark values or loop detections are displayed as if measured.

## Explicitly unexecuted

| Check | Status / reason |
|---|---|
| Native dependency/runner compilation | Not run; needs selected hosted Linux |
| Unit tests, Python runtime imports, lint/typechecks | Not run; prohibited on development PC |
| Frontend production build | Not run; preview compilation is not production verification |
| Calibration/FFprobe/FFmpeg/sample generation | Not run; hosted execution required |
| ORB vocabulary download / SLAM processing | Not run; no local model/data download or inference |
| Actual trajectory/landmark/loop correction | Unverified; real footage and hosted execution needed |
| Native patch concurrency/termination | Source inspected only; runtime/stress validation pending |
| HTTP upload/failure/lifecycle smoke | Scripts written; not run |
| Repeated 10-second benchmark / ATE / RPE | No measurements; performance/accuracy unverified |
| Docker build / Compose / Nginx / restart | Not run; final acceptance belongs on AWS |
| AWS cost, credits, region, quota / resource creation | Deferred; no resources created |
| Public URL / external-device test | Not available |

## Next evidence required

Select an existing Lightning Studio or AWS host, provide runtime access through an existing authenticated session/connection (never paste secrets), and supply a real ~10-second monocular clip plus a return-to-start loop clip. Run setup → native proof of concept → tests → real HTTP flow → repeated benchmark. Resolve compile/runtime failures before advancing. Docker/AWS acceptance remains a separate gate even if Lightning succeeds.

Append actual hosted commands/results here. Never mark a phase accepted solely because its files exist.

## 2026-09-19 — Lightning two-service recipe update (source only)

Prepared separate Lightning launchers for the API on 8000 and compiled frontend on 5173, a combined lifecycle wrapper, same-origin frontend proxying, a hosted/non-preview frontend configuration, pinned Node fallback installation with checksum verification, and updated Studio instructions. Assignment 1 files were not in this workspace and were not changed.

These changes were inspected only. Per repository policy, the Lightning setup, Node download, native build, vocabulary download, Python/npm installation, TypeScript/build checks, backend startup, proxy behavior, real video processing, public port exposure and public URL remain unexecuted/unverified until run in the selected Lightning Studio. The absence of a URL here is intentional; Lightning creates the real URL only after the account owner exposes the running Studio port.

## 2026-09-19 — user-reported Lightning configure failure

The user supplied a Lightning build log showing that g2o and FBoW had built, but stella_vslam configuration stopped when the installed g2o CMake package called `find_dependency(OpenGL)`. CMake specifically reported missing `OPENGL_opengl_LIBRARY`, `OPENGL_glx_LIBRARY` and `OPENGL_INCLUDE_DIR`. The installation recipes now include `libgl1-mesa-dev`, which supplies the GLVND/OpenGL/GLX development files on the targeted Ubuntu/Debian systems; the headless viewer remains disabled. Rerun outcome is pending and must be recorded rather than presumed successful.

## 2026-09-19 — user-reported Lightning venv restriction

After installing the native runner and pinned vocabulary successfully, the user's Lightning log showed that the platform rejected `python -m venv`: a Studio supplies one persistent Conda environment and prohibits creating another environment. The Lightning setup and launch scripts now discover and use the active Python 3.11+ interpreter directly. Compatibility with an existing `.venv` is retained for other hosted Linux environments. Python package installation, backend startup and later checks remain pending until the user resumes them in the Studio.

## Folder-based Lightning setup and startup

Added `setup-lightning.sh` and `run-lightning.sh` in both `backend/` and `frontend/`. Backend setup installs OS/native/vocabulary/Python dependencies and does not invoke npm. Frontend setup selects Node, installs npm dependencies and builds the hosted frontend without invoking Python or native compilation. The root Lightning setup delegates to these scripts. Requirements are resolved from `backend/`; npm runs from `frontend/`; shared assets remain at the project root.

Verified all eight added/modified deployment shell scripts with Git Bash `bash -n` on Windows (syntax parsing only; no commands in the scripts executed). Inspected launcher paths, hosted build script availability and updated instructions. The user reported the backend running before this refactor; the new folder scripts, hosted build, frontend proxy and public UI still require execution in the Studio. No backend, native build, unit tests, typecheck or production build was run on the development PC for this change.

## 2026-09-20 — final submission documentation

I rewrote the main README as an evaluator-facing Assignment 2 overview, added first-person AI disclosure, created dedicated Lightning AI and AWS deployment runbooks, and added a structured benchmark record. The Lightning installation logs supplied during deployment establish Python 3.12, Node 22.14.0, npm 10.9.2, CMake 3.28, OpenCV 4.6.0, OpenMP 4.5, spdlog 1.12.0, successful native runner installation, and pinned vocabulary retrieval.

I recorded the operator-supplied Lightning URL in the submission README. A new external request to its public `/api/health` endpoint returned HTTP 502 during this documentation pass. I therefore did not mark the public health check as passing; the Studio and both services must be running and the direct/proxied checks in `lightning/README.md` must pass before hand-in.

No five-run video-processing output, Studio CPU/RAM description, or AWS runtime evidence was supplied. I left those fields explicitly pending in `benchmarks/benchmark_results.md` rather than fabricating results.
