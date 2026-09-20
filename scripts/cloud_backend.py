#!/usr/bin/env python3
"""Shared hosted launcher. Neither target requires source patches."""
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))
os.chdir(ROOT)

if __name__ == "__main__":
    from app.config import Settings
    Settings.load().guard()
    import uvicorn
    uvicorn.run("app.main:create_app", factory=True, host=os.getenv("API_HOST", "127.0.0.1"),
                port=int(os.getenv("API_PORT", "8000")), workers=1, limit_concurrency=32,
                timeout_keep_alive=5, access_log=False)
