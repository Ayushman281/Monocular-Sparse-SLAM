#!/usr/bin/env python3
"""Real HTTP smoke checks against the hosted backend, including corrupt input."""
import argparse
import sys
import time
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend"))


def main():
    from app.config import Settings
    Settings.load().guard()
    import httpx
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--url", default="http://127.0.0.1:8000")
    parser.add_argument("--video", required=True, type=Path)
    args=parser.parse_args()
    with httpx.Client(base_url=args.url.rstrip("/"),timeout=150) as client:
        assert client.get("/api/health").json()["status"]=="healthy"
        assert client.post("/api/v1/slam/process",files={"video":("empty.mp4",b"")}).status_code==422
        bad=client.post("/api/v1/slam/process",files={"video":("corrupt.mp4",b"not a video")})
        bad.raise_for_status()

        def wait(job_id):
            deadline=time.monotonic()+330
            while time.monotonic()<deadline:
                response=client.get(f"/api/v1/slam/{job_id}")
                response.raise_for_status()
                data=response.json()
                if data["status"] in {"success","failed"}: return data
                time.sleep(.1)
            raise TimeoutError("Job did not finish")

        assert wait(bad.json()["job_id"])["status"]=="failed"
        with args.video.open("rb") as handle:
            good=client.post("/api/v1/slam/process",files={"video":(args.video.name,handle)})
        good.raise_for_status()
        result=wait(good.json()["job_id"])
        assert result["status"]=="success",result.get("error")
        assert result["result"]["slam"]["map_points"]>=10
        for artifact in ("trajectory.csv","pointcloud.ply","result.json"):
            assert client.get(f"/api/v1/slam/{good.json()['job_id']}/{artifact}").status_code==200
        print("Health, empty/corrupt input, actual video reconstruction and downloads passed.")


if __name__=="__main__": main()
