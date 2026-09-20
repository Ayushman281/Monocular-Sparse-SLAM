# Performance protocol

No baseline, tuning trial or final runtime measurement exists yet. The ≤10-second requirement is **not verified**. Never substitute Vite startup, frontend rendering, engine-paper timings or hypothetical outputs for actual server processing.

## Timing boundaries

- Browser upload+acceptance: POST dispatch until the server returns the job ID. Includes multipart parsing/storage, not just network transfer.
- Preprocessing: FFprobe, camera configuration and FFmpeg autorotation/CFR/resize/FFV1 normalization.
- SLAM process: process launch, vocabulary startup, native decode, feature extraction/tracking, mapping, queued/global optimization, native export and teardown.
- Postprocessing: parse and validate exports, display selection, trajectory CSV, video removal and initial JSON persistence.
- Total server: accepted, fully stored upload to completed initial result persistence. The final rewrite that updates timing fields and HTTP response transport are outside that timestamp; the independent observed-ready measurement covers them.
- Observed ready: benchmark POST response to receipt of the full terminal result JSON, including status polling and HTTP transfer. Polling at 50 ms makes this a conservative bound after the acceptance response; a small initial scheduling interval can overlap the POST response. No timing used as a playback delay.
- RTF = total server processing seconds / original video duration seconds.

For strict official acceptance require all five or more runs on a ~10-second video to have server seconds<=10, RTF<=1 and observed ready seconds<=10, plus useful geometry and adequate tracking coverage. This additional observed check avoids a borderline pass based on excluding final transport/persistence overhead.

## Initial settings, not optimized findings

| Parameter | Initial value | Reason to try it |
|---|---|---|
| Target FPS | 15, capped at source FPS | Around 150 frames for a 10-second clip |
| Longest dimension | 640 px | Bound both portrait and landscape processing cost |
| ORB levels | 8 | Multi-scale tracking starting point |
| `ORB_MIN_AREA` | 800 | Actual engine feature-density control |
| FAST threshold | 20 / fallback 7 | Engine-compatible starting point |
| Concurrent jobs | 1 | Isolate compute and avoid oversubscription |
| OpenMP threads | 2 | Tune against CPU quota; avoid unbounded thread fanout |
| Mapping waits | Local BA allowed to finish | Preserve useful map optimization before chasing latency |

The engine does not expose an `ORB_NUM_FEATURES` parameter in this revision. Do not add unused YAML keys and claim they tune it. Raising `ORB_MIN_AREA` generally reduces spatial feature density; evaluate geometry before adopting it.

## Measurements

Run the same uploaded clip through `scripts/benchmark.py`. The first run is retained; each job starts a new native process and loads its vocabulary, so report OS-cache warming separately if observed. Record every failed attempt. Native scheduling/RANSAC can vary results; compare ranges and coverage, not only means.

| Width bound | FPS | Thread count | Time | Map points | Tracking coverage | Decision |
|---|---|---|---|---|---|---|
| No experiments executed | — | — | — | — | — | Await hosted runtime |

Profile before tuning: FFmpeg/preprocessing vs native startup, decode, frame-feed time, queued optimization, export and Python serialization. Native `feed_seconds` includes waits for local mapping, so it is not exclusively ORB extraction. Parallel module timings overlap and must not be summed as independent CPU time.

Ensure Release and headless operation first. Then examine repeated vocabulary load and two-stage decoding, resolution/FPS, feature density and threading. Reusing a persistent native engine would change process isolation/lifecycle and requires profiling evidence and new tests. Never destroy tracking or disable all drift correction merely to reach a speed target. Do not declare success based on tiny/featureless inputs.

Only after a baseline choose the smallest AWS CPU configuration that meets the target. Record Docker CPU/memory limits, instance type and competing workloads; advertised vCPU count alone is insufficient.

## Accuracy, if ground truth becomes available

Use a suitable monocular sequence with camera calibration and synchronized reference poses (for example the RGB portion of a suitable TUM sequence). Align monocular estimates using Sim(3) when evaluating up-to-scale accuracy. ATE measures global aligned trajectory discrepancy; RPE measures motion error over intervals. Report alignment, sampling, missing frames and coordinate conventions. Do not quote ATE/RPE without reference data and actual evaluation. Dataset protocols differ; EuRoC's IMU/body trajectory may need an extrinsic transform to the camera frame.
