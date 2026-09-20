# Offline completion patch

Upstream: stella_vslam 0.7.0, `525231147319bcd31242f981078c36d9272727b4`.

I added `system::wait_for_pending_work(timeout_seconds)` and small queue/active-worker state hooks in mapping and global optimization through `offline-drain.patch`. Upstream shutdown requests termination without guaranteeing that every queued keyframe has been processed, so I do not let the offline exporter skip the final loop-detection queue or export during map correction.

Call this method only after the last frame feed has returned, with no concurrent reset/feed/manual-loop requests. Mapping remains active until it has handed its processed keyframe to global optimization. Global work remains active across candidate detection and correction. A separate flag covers loop BA from **before thread launch to after optimize returns**, closing the thread-start race before its internal running flag becomes visible. Queue state and flags are read/written under their existing mutexes. The synchronization wait is 1 ms and is not tied to video timestamps. All wait time is included in native and server timings.

After drain succeeds, the runner shuts down and exports the engine's corrected TUM trajectory plus world landmarks. If the drain deadline expires, the job fails instead of exporting an apparently final map. The parent process deadline terminates hung workers.

I did not use this patch to implement a substitute algorithm, alter optimization mathematics, or create provider-specific behavior. I preserve the upstream license notices and use the same patch on both providers. I inspected source-only patch compatibility locally; I require hosted native compilation, race/lifecycle tests, and a real loop-return demonstration for runtime evidence.

The hosted build script runs `git apply --check` before applying the patch. Record upstream revision, patch SHA256 and source/build logs in benchmark provenance. Never replace the engine with an older version to make this API compile.
