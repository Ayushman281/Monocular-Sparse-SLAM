# Assignment 2 Benchmark Record

This document is the authoritative location for measured processing time and test-environment evidence. It separates verified observations from fields that still require runtime capture.

## Measurement status

The available installation logs identify several toolchain versions but do not contain a completed five-run video-processing benchmark. Processing-time claims therefore remain unverified until the generated benchmark evidence is entered below.

## Test environment

| Field | Recorded value |
|---|---|
| Platform | Lightning AI Studio |
| Benchmark date (UTC) | Pending |
| Studio machine type | Pending |
| CPU model / vCPUs / RAM | Pending |
| Operating system | Pending |
| Python | 3.12, Lightning `cloudspace` Conda environment |
| Node.js / npm | 22.14.0 / 10.9.2 |
| CMake | 3.28 |
| OpenCV | 4.6.0 |
| OpenMP | 4.5 |
| spdlog | 1.12.0 |
| SLAM engine | stella_vslam 0.7.0 at `525231147319bcd31242f981078c36d9272727b4` plus `offline-drain.patch` |
| Application commit | Pending |

## Input and processing configuration

| Field | Recorded value |
|---|---|
| Input filename / SHA-256 | Pending |
| Duration / resolution / source FPS | Pending |
| Camera calibration mode | Pending |
| Processing width / FPS | Pending |
| ORB configuration / OpenMP threads | Pending |

## Benchmark command

```bash
cd /teamspace/studios/this_studio/Monocular-Sparse-SLAM
export EXECUTION_TARGET=lightning
export ENABLE_SLAM=true
python scripts/benchmark.py \
  --video /path/to/approximately-10-second-video.mp4 \
  --runs 5
```

Use `--official` only from a clean committed checkout with an input duration accepted by the benchmark script.

## Per-run results

| Run | Server processing | Observed ready | Native SLAM | RTF | Tracked / processed | Keyframes | Map points | Loop edges | Result |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|
| 1 | Pending | Pending | Pending | Pending | Pending | Pending | Pending | Pending | Pending |
| 2 | Pending | Pending | Pending | Pending | Pending | Pending | Pending | Pending | Pending |
| 3 | Pending | Pending | Pending | Pending | Pending | Pending | Pending | Pending | Pending |
| 4 | Pending | Pending | Pending | Pending | Pending | Pending | Pending | Pending | Pending |
| 5 | Pending | Pending | Pending | Pending | Pending | Pending | Pending | Pending | Pending |

## Summary

| Metric | Result |
|---|---|
| Successful runs | Pending |
| Server time: mean / median / minimum / maximum | Pending |
| Mean observed-ready time | Pending |
| Mean real-time factor | Pending |
| All required runs at or below 10 seconds | **Unverified** |
| Useful reconstruction in every accepted run | **Unverified** |

The benchmark script stores raw results, `environment.json`, and `summary.json` under `benchmarks/runs/<UTC-date>/`. Retain failed and slow runs, bind results to the exact source revision and input hash, and exclude private video content from published evidence.
