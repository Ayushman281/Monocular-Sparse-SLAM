# Assignment 2 Performance Measurement

Assignment 2 requires measured processing time and a description of the test environment. This document defines the measurement procedure and the information that must accompany a reported result.

## Environment information available from installation logs

| Component | Observed value |
|---|---|
| Platform | Lightning AI Studio |
| Python | 3.12, Lightning `cloudspace` Conda environment |
| Node.js / npm | 22.14.0 / 10.9.2 |
| CMake | 3.28 |
| OpenCV | 4.6.0 |
| OpenMP | 4.5 |
| spdlog | 1.12.0 |
| SLAM engine | stella_vslam 0.7.0 at `525231147319bcd31242f981078c36d9272727b4` plus `offline-drain.patch` |

## Measurement command

Run the following command on the same Lightning Studio as the backend, using an approximately ten-second monocular RGB video:

```bash
cd /teamspace/studios/this_studio/Monocular-Sparse-SLAM
export EXECUTION_TARGET=lightning
export ENABLE_SLAM=true
python scripts/benchmark.py \
  --video /path/to/approximately-10-second-video.mp4 \
  --runs 5
```

Use `--official` only from a clean committed checkout with an input duration accepted by the benchmark script.

## Required result fields

A submitted measurement should include:

- benchmark date and application commit;
- Studio machine type, CPU model, vCPU count, RAM, and operating system;
- input SHA-256, duration, resolution, and source frame rate;
- camera mode, processing resolution/FPS, ORB settings, and OpenMP thread count;
- all per-run server, observed-ready, and native-SLAM times;
- real-time factor, tracking coverage, keyframes, map points, and loop edges; and
- mean, median, minimum, and maximum processing time.

The benchmark script stores raw run data, `environment.json`, and `summary.json` under `benchmarks/runs/<UTC-date>/`.

## Result status

No completed five-run benchmark output was supplied for inclusion in this repository. Consequently, the submission does not state a measured processing-time value or claim that a timing threshold has passed. This avoids presenting an estimated or fabricated result as measured evidence.
