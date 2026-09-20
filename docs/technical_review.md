# Technical review preparation

Use these as explanations to understand and adapt. Demonstrate actual code and measured output; do not rehearse claims of benchmarks or deployment that have not happened.

| # | Question | Answer to understand |
|---|---|---|
| 1 | What is SLAM? | Simultaneously estimate a camera's motion and a map of its surroundings from observations. |
| 2 | SLAM vs visual odometry? | VO estimates incremental motion; this SLAM system also maintains/reuses landmarks and keyframes and corrects the map through optimization and loops. |
| 3 | Why monocular? | The assessment supplies one RGB camera. It is accessible but loses direct metric depth/scale. |
| 4 | Scale ambiguity? | Scaling all positions and translations together leaves the same image projections. |
| 5 | Why not metres? | There is no known metric baseline, external distance, depth sensor or IMU constraint. |
| 6 | Calibration? | Estimate the mapping from rays to pixels, including lens distortion. |
| 7 | fx/fy/cx/cy? | Pixel focal lengths in the two axes and principal-point coordinates. |
| 8 | Distortion coefficients? | Radial and tangential deviations from ideal pinhole projection. |
| 9 | Incorrect calibration? | It changes predicted rays and projections, biasing poses and triangulation. |
| 10 | ORB? | Oriented FAST corners and rotated binary descriptors, extracted across an image pyramid. |
| 11 | Why ORB? | Compact descriptors and efficient matching suit native sparse tracking; not robust to every scene. |
| 12 | Descriptor? | A compact representation of local image appearance around a keypoint. |
| 13 | Matching? | Compare binary descriptors using Hamming distance, then enforce geometric consistency and reject outliers. |
| 14 | Essential matrix? | A two-view relation for calibrated rays, encoding relative rotation and translation direction, not metric scale. |
| 15 | RANSAC? | Fit multiple hypotheses from small subsets and choose one supported by many geometrically consistent observations. |
| 16 | Relative pose? | Two-view geometry supplies candidates; triangulation/parallax and positive-depth checks select a viable solution. |
| 17 | Triangulation? | Recover a point from rays observed at different camera poses. |
| 18 | Map point? | A persistent 3D landmark associated with descriptor and observations across keyframes. |
| 19 | Keyframe? | An informative retained frame used to maintain and optimize the map. |
| 20 | Why not every frame? | Redundant views increase memory and BA cost without proportional geometric information. |
| 21 | PnP? | Estimate a camera pose from 3D landmarks and corresponding 2D observations. |
| 22 | Reprojection error? | Difference between an observed image feature and where the current pose/map predict it should project. |
| 23 | Bundle adjustment? | Jointly refine camera poses and 3D points to reduce reprojection error. |
| 24 | Optimized variables? | Poses and landmark coordinates; this configured application holds camera intrinsics fixed. |
| 25 | Loop closure? | Recognize a previously mapped place and add a verified constraint that corrects accumulated inconsistency. |
| 26 | Loop detection? | FBoW appearance proposals, exclusion/continuity checks and geometric verification in stella. |
| 27 | Pose graph? | Poses are graph nodes; measured relative relations constrain their mutual consistency. |
| 28 | How loops reduce drift? | A revisit ties together distant path portions and distributes correction over connected poses/map points. |
| 29 | Completely remove drift? | No. Noise, false associations, unobservable directions and limited revisits remain. |
| 30 | Why monocular drift? | Small estimation errors compound; global position, rotation and scale can drift without external constraints. |
| 31 | Pure rotation? | It changes viewing direction but supplies no translational baseline for new reliable depth. |
| 32 | Textureless scene? | Insufficient repeatable features; initialization/tracking can fail. |
| 33 | Moving objects? | They violate the static-scene assumption. Robust estimation may reject some, but dominant motion can corrupt tracking. |
| 34 | Motion blur? | Features/descriptors become less repeatable and geometric correspondences degrade. |
| 35 | Why stella? | A pinned modern native sparse SLAM engine matches the required mapping/optimization/loop architecture. |
| 36 | Why not from scratch? | Implementing and validating robust SLAM would add substantial risk without serving the assessment's app/deployment goals. |
| 37 | Why not DROID? | It adds learned-model/GPU dependencies; there is no measured advantage for this CPU sparse-map scope. |
| 38 | Why no GPU? | The selected classical pipeline is CPU-oriented. CPU sufficiency still requires measurement. |
| 39 | Why FastAPI? | Typed validation, HTTP routing, async job orchestration and a small Python service boundary. |
| 40 | Why C++? | Keep frame tracking, matching, map updates and nonlinear optimization in the native engine. |
| 41 | Why React? | It manages upload, settings, polling and result state in a browser-friendly UI. |
| 42 | Why WebGL/Three.js? | Render sparse 3D points and trajectory interactively without a native client. Three.js is the chosen allowed alternative to Plotly. |
| 43 | Why Docker? | Package native dependencies and web services into a reproducible deployment recipe; it does not itself prove portability or performance. |
| 44 | Why EC2? | The assignment requires AWS, and a single CPU host can run this compact architecture. |
| 45 | Why this AWS instance? | None selected yet. Answer from actual CPU benchmark, quota, region and verified total cost after selection. |
| 46 | How was <=10 seconds met? | It has not been verified. Show real repeated benchmark evidence before making this claim. |
| 47 | Largest bottleneck? | Unknown pending profiling. We measure preprocessing, startup, feed, optimization drain and export separately. |
| 48 | Why resize? | Bound image processing cost; scale intrinsics consistently to avoid geometry errors. |
| 49 | Why sample FPS? | Reduce frame work while trying to retain overlap and usable parallax. |
| 50 | Accuracy tradeoff? | Fewer/smaller images can lose feature support or motion continuity; inspect tracking and map quality alongside time. |
| 51 | Evaluate accuracy? | Synchronize reference and estimates, resolve frame conventions, align monocular scale consistently, then calculate actual ATE/RPE. |
| 52 | ATE? | Absolute trajectory error after the specified alignment, reflecting global trajectory agreement. |
| 53 | RPE? | Relative pose error over a stated interval, reflecting local motion/drift error. |
| 54 | TUM/KITTI/EuRoC? | Select monocular-compatible data, exact intrinsics and frame transforms; respect dataset timestamps and evaluation protocol. No results measured yet. |
| 55 | Add IMU? | Requires synchronization, camera–IMU calibration, sensor noise/bias models and a supported visual-inertial estimator. |
| 56 | Recover metric scale? | Introduce a known geometric distance, stereo baseline, external position or well-calibrated inertial constraints. |
| 57 | Multiple users? | First benchmark safe concurrency. Durable queue/workers/storage are justified only when scale exceeds this one-process design. |
| 58 | Prevent exhaustion? | Bound body size, duration/resolution, active jobs, native timeout, retained jobs and container resources. |
| 59 | Native crash? | Check exit code, stop child process groups on timeout, mark the job failed, clean videos and preserve bounded-lifetime diagnostics. |
| 60 | AI assistance? | Codex authored/assisted source, docs and preview inspection; the engineer must verify native behavior and measurements. See AI_USAGE.md. |

## Trace a result through the source

Start in `frontend/src/App.tsx`: `FormData` → `POST /api/v1/slam/process`. Follow `backend/app/main.py` admission/validation → `jobs.py` stage changes → `video.py`/`camera.py` → subprocess args → `slam/src/main.cpp` engine feeding/drain/export → `results.py` checks → polling response → `Viewer.tsx` geometry. Explain why no backend path returns a synthetic success.

Point to the transform test where `-Rᵀt` maps the camera center back to the camera origin. Explain that CSV uses `Twc`; quaternions are `qx,qy,qz,qw`. Explain that point colors only distinguish geometry/trajectory. A loop count of zero is valid; a loop count above zero is not automatically an accuracy metric.

## Modification exercises

| Level | Exercise | Where the change propagates and what to verify |
|---|---|---|
| Easy | Change duration/FPS limits | `.env` → Settings → metadata/normalization → system endpoint and UI; benchmark again. |
| Easy | Reduce displayed point limit | Settings → deterministic result subset → WebGL; full PLY should retain the valid map. |
| Easy | Add a result summary label | Result schema/type → App rendering; only display an actual field. |
| Medium | XZ top-down trajectory | Use existing `Twc` positions; show relative units, identical frame conventions and lost gaps. |
| Medium | Keyframe markers | `keyframe_trajectory` already exists; sample camera frustums and dispose Three geometries correctly. |
| Medium | Resolution selector | Validated request option → preprocessing dimensions → scaled calibration → native matching → benchmark provenance. |
| Medium | Tracking percentage | Tracked/processed count → result and UI; distinguish online frames from final retained poses. |
| Hard | Cancellation | Explicit API → task cancellation → process-group kill → terminal status → video cleanup → UI recovery. |
| Hard | ATE against ground truth | Timestamp association → coordinate conversion → stated Sim(3) alignment → metrics and missing-track coverage. |
| Hard | Loop visualization | Instrument actual accepted loop events and graph edges; no inferred or animated fake closures. |
| Hard | Visual-inertial support | New sensor/calibration/backend capabilities and tests; not merely a frontend option. |

Exports, asynchronous processing and custom intrinsics already exist, so review their implementation instead of presenting them as future features. Explain every change in terms of geometry, state, runtime cost and the evidence needed to trust it.
