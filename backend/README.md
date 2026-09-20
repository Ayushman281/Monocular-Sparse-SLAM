# Backend on Lightning AI

I keep the complete project together because this folder's scripts also use `../slam`, `../scripts` and `../lightning`.

From this `backend/` folder, I install the OS libraries, native SLAM, vocabulary, and Python dependencies:

```bash
BUILD_JOBS=2 bash setup-lightning.sh
```

Setup uses the Studio's existing Conda Python 3.11+ and does not create a venv or install frontend packages. To update only Python dependencies after native installation:

```bash
python -m pip install -r requirements-test.txt
```

I start the API on port 8000:

```bash
ENABLE_SLAM=true bash run-lightning.sh
```

Keep it running. From another terminal, check:

```bash
curl --fail http://127.0.0.1:8000/api/health
```

Expect `status: healthy`, `slam_runner_available: true` and `slam_enabled: true`. Health checks confirm service readiness; test a real upload to verify reconstruction. See [the complete Studio guide](../lightning/README.md).
