# Demonstration and Benchmark Videos

Video files are intentionally excluded from source control to avoid committing large or private media. Approved demonstration footage should be distributed as a separate submission asset when required.

## Benchmark clip

Recommended properties for `benchmark.mp4`:

- approximately 10 seconds long;
- static, textured, and well-lit scene;
- slow camera motion with meaningful translation;
- fixed lens, zoom, resolution, and orientation; and
- retained original file for hashing and provenance.

Avoid pure panning, digital zoom, abrupt exposure changes, moving people, scene cuts, heavy stabilization, and motion blur. When available, use camera calibration captured with the same lens, zoom, resolution, and orientation.

Record the capture device/settings, input SHA-256, duration, resolution, source FPS, calibration mode, processing settings, and license/consent status with the benchmark evidence.

## Loop-return clip

For `loop-return.mp4`, begin at a visually distinctive location, move through the environment, and revisit the starting area with sufficient overlap. A physical revisit is necessary but does not guarantee that the engine will accept a loop closure. Evaluate the actual loop-edge count and corrected trajectory/map output.

## Data-integrity policy

- Do not introduce synthetic points or trajectories as evidence of successful reconstruction.
- Preserve unsuccessful or slow benchmark runs.
- Keep private footage and calibration images outside source control.
- Include only approved, shareable media in the final submission package.
