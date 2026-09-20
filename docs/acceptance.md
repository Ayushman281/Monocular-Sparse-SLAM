# Final acceptance — not yet passed

Every unchecked item needs runtime evidence. Do not mark completion on source review alone.

## Functional / SLAM

- [ ] Public app loads and accepts a real monocular video.
- [ ] Actual media metadata, calibrated and fallback intrinsics work.
- [ ] Native SLAM initializes, tracks motion, triangulates landmarks and maps keyframes.
- [ ] Local BA and geometric rejection operate; final correction is drained before export.
- [ ] Real return-to-start footage produces verified loop evidence, or the limitation is recorded without inventing a detection.
- [ ] Corrected `Twc` trajectory, PLY and JSON are consistent and downloadable.
- [ ] Rotate, zoom, pan, start/end and sparse geometry work with actual outputs.
- [x] Arbitrary-scale warning is visible in the verified interface preview.
- [ ] Real output gaps, mapping quality and tracked-frame ratio are inspected.

## Robustness

- [ ] Empty, corrupt, unsupported, over-limit and zero-frame videos fail safely.
- [ ] Textureless, pure-rotation, blurred and low-motion inputs have useful failure UX.
- [ ] Invalid intrinsics/orientation/dimensions are rejected.
- [ ] Native crash and hung process produce safe errors; subprocesses are killed.
- [ ] Concurrent upload attempts are bounded and rejected promptly.
- [ ] Videos, orphan jobs and old artifacts are cleaned; no active job is evicted.
- [ ] Server restart recovers health, with documented loss of in-memory job state.

## Performance / deployment

- [ ] Actual ~10-second clip, input hash, calibration and exact host documented.
- [ ] Five or more runs recorded, including startup/preprocessing/optimization/export.
- [ ] Every official run meets <=10 seconds and RTF<=1 with useful geometry.
- [ ] Docker build/start/health/Nginx/restart tested on AWS.
- [ ] AWS account costs, credits, region, quota and maximum test budget verified before creation.
- [ ] AWS public URL verified from another device/network; same source works on Lightning.

## Submission

- [x] README, architecture, pipeline, AI usage, notices, license, setup recipes and review guide prepared.
- [ ] Benchmark report filled with actual results and deployment steps rewritten as tested steps.
- [ ] Source/ZIP reflects the demonstrated revision; no credentials or private sample footage included.
- [ ] Final public URL placed in README; all limitations and unexecuted checks remain honest.
