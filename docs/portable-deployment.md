# AWS / Lightning portability

The native library, C++ runner, Python API and frontend are shared. Environment changes select deployment behavior; provider-specific model code is absent.

| Setting | Lightning native | AWS Docker |
|---|---|---|
| `EXECUTION_TARGET` | `lightning` | `aws` |
| `ENABLE_SLAM` | Explicitly `true` for execution | Explicitly `true` in `.env` |
| `SLAM_RUNNER` | `$PROJECT/.local/slam/bin/slam_runner` | `/opt/slam/bin/slam_runner` |
| `SLAM_VOCAB` | `$PROJECT/.local/slam/share/orb_vocab.fbow` | `/opt/slam/share/orb_vocab.fbow` |
| `LD_LIBRARY_PATH` | Shared prefix `lib` | `/opt/slam/lib` |
| Frontend serving | Vite preview of compiled assets on 5173 | Nginx |
| Browser API | Same-origin `/api` | Same-origin `/api` |
| External port | Studio frontend 5173; API 8000 stays private by default | Nginx 80/443 |
| Result storage | Studio `data/jobs` | Bounded container `/tmp` |

`frontend/public/app-config.json` deliberately declares local preview mode. The hosted build selects `frontend/public-hosted/app-config.json`, which enables processing with a relative API base. The Lightning frontend proxies `/api` to `127.0.0.1:8000`; Nginx does the equivalent inside Docker. No embedded Lightning hostname, model-provider credential or backend CORS wildcard is required.

`scripts/cloud_backend.py` is the Assignment 2 shared launcher. The parent workspace's identically named launcher belongs to Assignment 1; run commands from this subproject. Native libraries must be on the dynamic linker path. Both hosts must use the dependency revisions and patch recorded in `slam/`.

Native and Docker packaging may resolve different distribution library patch versions. Record the installed package manifest and benchmark the final Docker container; native Lightning success alone is not AWS Docker acceptance. Cloud resources, app sleeping behavior, resource limits and proxy routing differ even when application source is identical.

Environment flags are fail-closed defaults, not permission to run the backend on an arbitrary Linux computer. Only select `aws` or `lightning` on the actual authorized hosted environment.
