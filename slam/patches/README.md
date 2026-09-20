# Offline-Completion Patch

## Upstream target

- Engine: stella_vslam 0.7.0
- Revision: `525231147319bcd31242f981078c36d9272727b4`
- Patch: `offline-drain.patch`

## Purpose

Upstream shutdown requests termination but does not guarantee that every queued keyframe has completed mapping and global-optimization work. Exporting immediately after the last frame can therefore omit final loop-detection work or capture a map while correction is still active.

The patch adds:

- `system::wait_for_pending_work(timeout_seconds)`;
- queue-state checks for mapping and global optimization;
- active-worker state tracking; and
- loop-bundle-adjustment state tracking from before thread launch until optimization returns.

## Synchronization contract

Call `wait_for_pending_work` only after the final frame feed returns and when no reset, feed, or manual-loop request can run concurrently. Mapping remains active until the processed keyframe has been handed to global optimization. Global work remains active throughout candidate detection and correction.

Queue state and activity flags use their existing mutexes. The wait interval is 1 ms and is independent of video timestamps. All wait time is included in native and server processing measurements.

After a successful drain, the runner shuts down and exports the corrected TUM trajectory and world landmarks. If the drain deadline expires, the job fails instead of exporting an apparently final map. The parent-process deadline remains responsible for terminating a hung native process.

## Scope

The patch does not replace the SLAM algorithm, alter optimization mathematics, or introduce provider-specific behavior. The same native source is used on Lightning AI and AWS, and upstream license notices are preserved.

## Build and verification

The hosted build script runs `git apply --check` before applying the patch. Benchmark provenance should record the upstream revision, patch SHA-256, build logs, and runtime evidence. Native compilation, lifecycle/race testing, and a real loop-return demonstration are required before treating the behavior as verified.
