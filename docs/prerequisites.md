# Prerequisites and execution boundaries

Checked on the development PC on 2026-09-19 using version/path inspection only:

| Tool | Observed |
|---|---|
| `wsl --version` | WSL 2.5.7.0; no Linux workload launched |
| `git --version` | 2.49.0.windows.1 |
| `docker --version` | Not on Windows PATH; not run |
| `python --version` | 3.12.10 |
| `node --version` | v22.15.0 |
| `npm.cmd --version` | 10.9.2 |
| `cmake --version` | Not on Windows PATH; not run |
| `g++ --version` | Not on Windows PATH; not run |
| `ffmpeg -version` | Not on Windows PATH; not run |

WSL normally provides a useful Linux C++ environment, but this project's current policy explicitly prohibits backend execution on the development PC, including WSL. No local C++/Docker toolchain was installed. Python 3.11 is used in Docker; a compatible hosted Python 3.11/3.12 interpreter can use the native launcher.

For frontend preview, the existing Node version is sufficient. `npm.cmd ci --ignore-scripts` installs locked frontend dependencies. Only `npm.cmd run dev -- --port 5174` is authorized here; the `build` script runs TypeScript checking and belongs on the hosted runtime.

On Lightning, use `bash setup-lightning.sh` from `backend/`, then the same command from `frontend/`. Each installs only that service's dependencies. See the [folder-based Lightning workflow](../lightning/README.md).

On an explicitly selected AWS Debian 12 or Ubuntu 22.04/24.04 host, with Python 3.11+, the native setup from the project root is:

```bash
export EXECUTION_TARGET=aws
bash scripts/install_system.sh
bash scripts/build_native.sh
bash scripts/download_vocab.sh
python3 -m venv .venv
.venv/bin/pip install -r backend/requirements-test.txt
```

The installation script installs compiler, CMake/Ninja, Git, curl, FFmpeg, Eigen, OpenCV, yaml-cpp, SQLite, SuiteSparse, spdlog, the OpenGL/GLX development interface required by g2o's exported CMake package, xz and Python venv support. The headless application does not open an OpenGL window. g2o/FBoW/stella are fetched at pinned revisions and built by the next script. CMake 3.x is targeted; the Debian 12 image avoids unvalidated CMake 4 policy changes. Start with two compile jobs to limit memory use.

`lightning/setup.sh` requires Python 3.11+ and installs packages into Lightning's existing persistent Conda environment because a Studio permits only one environment and rejects nested venv creation. It selects a compatible system Node or downloads the pinned official Node 22.15.0 binary, verifies it against the official SHA-256 manifest, runs `npm ci`, and makes the hosted frontend build. Hosted OS/distro variants and package names still require an actual build check. Do not report these recipes as tested installation steps until logs exist.

Docker is needed only for AWS acceptance. Follow the official [Docker Engine Ubuntu installation](https://docs.docker.com/engine/install/ubuntu/) and Compose plugin instructions there on the selected server. Do not create resources merely to fill a prerequisite checklist.
