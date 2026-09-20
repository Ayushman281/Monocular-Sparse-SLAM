import asyncio
import os
import sys
import time
from dataclasses import replace
import pytest
from fastapi.testclient import TestClient
from app.config import Settings
from app.errors import JobError
from app.jobs import JobManager
from app.main import create_app
from app.process import run_process


def test_health_never_runs_slam(tmp_path):
    settings=replace(Settings.load(),enabled=True,jobs=tmp_path,runner=tmp_path/"missing",vocab=tmp_path/"missing-vocab")
    with TestClient(create_app(settings)) as client:
        assert client.get("/api/health").json()["slam_runner_available"] is False
        assert client.post("/api/v1/slam/process").status_code == 503
        assert client.get("/api/v1/slam/unknown/../../etc/passwd").status_code == 404


def test_concurrency_admission_and_cleanup(tmp_path):
    manager=JobManager(replace(Settings.load(),jobs=tmp_path,concurrency=1,ttl=1))
    job=manager.reserve()
    with pytest.raises(JobError,match="another upload"): manager.reserve()
    manager.cleanup()
    assert job.directory.exists()  # Active uploads must never be removed by TTL.
    job.completed=time.time()-2
    manager.active.remove(job.id)
    manager.cleanup()
    assert not job.directory.exists()


def test_timeout_kills_native_subprocess(tmp_path):
    pid_file=tmp_path/"pid"
    # A sleeping process is a lifecycle fixture, never a production SLAM response.
    code="import os,time,pathlib;pathlib.Path(%r).write_text(str(os.getpid()));time.sleep(60)" % str(pid_file)
    with pytest.raises(JobError,match="timed out"):
        asyncio.run(run_process([sys.executable,"-c",code],tmp_path/"process.log",.5))
    if pid_file.exists():
        with pytest.raises(ProcessLookupError): os.kill(int(pid_file.read_text()),0)


def test_explicit_execution_opt_in_required():
    with pytest.raises(RuntimeError): replace(Settings.load(),target="disabled",enabled=False).guard()
