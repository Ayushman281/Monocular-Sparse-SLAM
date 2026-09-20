import csv
import json
import pytest
from app.errors import JobError
from app.results import parse_results


def fixture_exports(directory):
    # Fixed parser fixtures only. Production routes always invoke the native engine.
    (directory/"stats.json").write_text(json.dumps({"status":"success", "optimization_complete":True,
        "pose_convention":"Twc", "scale":"arbitrary", "map_components":1,
        "map_points":12,"frames_tracked":3,"frames_processed":4}))
    (directory/"trajectory.tum").write_text("0 0 0 0 0 0 0 1\n0.1 1 0 0 0 0 0 1\n0.3 3 0 0 0 0 0 1\n")
    (directory/"keyframes.tum").write_text("0 0 0 0 0 0 0 1\n0.3 3 0 0 0 0 0 1\n")
    with (directory/"landmarks.csv").open("w",newline="") as handle:
        writer=csv.writer(handle);writer.writerow(["x","y","z","observations"])
        for index in range(12): writer.writerow([index,1,3,2])


def test_subsample_retains_endpoints_and_full_cloud(tmp_path):
    fixture_exports(tmp_path)
    original=(tmp_path/"landmarks.csv").read_bytes()
    result=parse_results(tmp_path,3)
    assert len(result["points"])==3
    assert result["points"][0]==[0,1,3] and result["points"][-1]==[11,1,3]
    assert (tmp_path/"landmarks.csv").read_bytes()==original
    assert result["trajectory"][2][0]==.3  # Lost time gap was not synthesized/interpolated.
    rows=list(csv.DictReader((tmp_path/"trajectory.csv").open()))
    assert [r["is_keyframe"] for r in rows]==["1","0","1"]


def test_multiple_gauges_and_nonfinite_points_are_rejected(tmp_path):
    fixture_exports(tmp_path)
    stats=json.loads((tmp_path/"stats.json").read_text());stats["map_components"]=2
    (tmp_path/"stats.json").write_text(json.dumps(stats))
    with pytest.raises(JobError,match="invalid"):parse_results(tmp_path,10)
    fixture_exports(tmp_path)
    with (tmp_path/"landmarks.csv").open("a") as handle:handle.write("nan,0,0,3\n")
    with pytest.raises(JobError,match="invalid"):parse_results(tmp_path,10)
