# Technical requirements checklist

Unchecked boxes are acceptance work, even where source exists.

## Functional

- [ ] Upload one monocular RGB MP4/MOV/AVI/WebM through React.
- [ ] Validate actual media, byte/duration/resolution limits, orientation and FPS.
- [ ] Calibrated and approximate camera modes produce usable configurations.
- [ ] Produce real camera poses, trajectory CSV, point cloud PLY and result JSON.
- [ ] Visualize actual points and trajectory with orbit, zoom, pan and reset.
- [ ] Explain invalid input, calibration mismatch, initialization/tracking failure and overload.
- [ ] Bound concurrent jobs, upload/processing time, memory/disk retention; remove videos.

## SLAM

- [x] Pin stella_vslam >=0.3 and inspect actual C++ APIs (0.7.0 pinned).
- [ ] Demonstrate ORB extraction, tracking, triangulation and persistent landmarks.
- [ ] Demonstrate keyframe insertion and local bundle adjustment.
- [ ] Demonstrate loop detection plus geometric verification and graph correction on a revisit clip.
- [ ] Confirm final export follows optimization completion and one common coordinate gauge.
- [ ] Validate transforms and distinguish `Tcw` from `Twc`.
- [x] Show arbitrary-scale warning in frontend; include exact limitation in README.
- [ ] Inspect real output coverage, outliers and camera motion with no invented geometry.

## Performance

- [ ] Record ~10-second official input hash, calibration and source resolution/FPS.
- [ ] Record CPU/vCPU/RAM/OS, Docker/native configuration and exact application/engine revision.
- [ ] Measure at least five runs, including preprocessing, vocabulary startup, SLAM, optimization and serialization.
- [ ] Each accepted official run has total server processing <=10 seconds, RTF<=1 and observed ready time<=10 seconds.
- [ ] Record failures and actual accuracy/performance tradeoffs; no omitted slow runs.

## Deployment

- [ ] Validate native application on selected hosted runtime.
- [ ] Validate Release native build, Docker Compose, Nginx and restart on AWS.
- [ ] Before resource creation verify account plan/credits, region/quota, price and total test budget; configure alerts.
- [ ] Expose only Nginx HTTP/HTTPS and restricted administrative access.
- [ ] Verify public AWS URL from another device/network.
- [ ] Re-run benchmark on exact public-deployment machine and container limits.
- [ ] Verify switching AWS/Lightning needs environment changes only.

## Documentation/submission

- [x] Create README, architecture, SLAM pipeline, limitations, performance protocol and technical review guide.
- [x] Create dependency lock, notices, licenses and AI usage record.
- [x] Initialize independent Git repository and secret/data ignore rules.
- [ ] Fill benchmark report with actual measurements and environment evidence.
- [ ] Record tested AWS steps, public URL, source revision and final checklist evidence.
