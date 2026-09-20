# Assignment 2 benchmark record

I use this document to report measured processing time and the exact environment in which I obtained it. I do not substitute UI startup time, a hypothetical value, or a single successful run for a repeated SLAM benchmark.

## Current measurement status

I have not been given a completed five-run benchmark output to place in this source package. The installation logs establish the toolchain details below, but they do not contain video-processing times. I will replace the pending fields with the generated evidence before claiming that the performance requirement passed.

| Environment field | Recorded value |
|---|---|
| Platform | Lightning AI Studio |
| Test date | Pending |
| Studio machine / CPU / vCPUs / RAM | Pending |
| OS | Pending |
| Python | 3.12, Lightning `cloudspace` Conda environment |
| Node.js / npm | 22.14.0 / 10.9.2 |
| CMake | 3.28 |
| OpenCV | 4.6.0 |
| OpenMP | 4.5 |
| spdlog | 1.12.0 |
| SLAM engine | stella_vslam 0.7.0, commit `525231147319bcd31242f981078c36d9272727b4` plus `offline-drain.patch` |
| Application commit | Pending |
| Input name / SHA-256 | Pending |
| Input duration / resolution / FPS | Pending |
| Camera mode / processing width / FPS | Pending |

## Command I use

```bash
cd /teamspace/studios/this_studio/monocular-sparse-slam-source/monocular-sparse-slam
export EXECUTION_TARGET=lightning
export ENABLE_SLAM=true
python scripts/benchmark.py \
  --video /path/to/approximately-10-second-video.mp4 \
  --runs 5
```

## Per-run results

| Run | Server processing | Observed ready | Native SLAM | RTF | Tracked/processed frames | Keyframes | Map points | Loop edges | Outcome |
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
| Mean / median / minimum / maximum server time | Pending |
| Mean observed-ready time | Pending |
| Mean real-time factor | Pending |
| Every required run ≤ 10 seconds | **Unverified** |
| Useful reconstruction in every accepted run | **Unverified** |

The benchmark script writes `environment.json`, raw per-run records, and `summary.json` under `benchmarks/runs/<UTC-date>/`. I will retain failures and slow runs, record the exact source revision, and copy the approved values here without including private video data.
