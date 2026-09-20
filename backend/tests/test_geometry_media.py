import math
import numpy as np
import pytest
from app.camera import CameraOptions, camera_config
from app.config import Settings
from app.errors import JobError
from app.results import camera_center, read_tum
from app.video import metadata_from_probe


def source(**updates):
    stream = {"codec_type":"video", "codec_name":"h264", "width":1920, "height":1080, "duration":"10", "avg_frame_rate":"30/1"}
    stream.update(updates)
    return {"streams":[stream], "format":{"format_name":"mov,mp4,m4a,3gp,3g2,mj2", "duration":"10"}}


def test_camera_center_is_not_world_to_camera_translation():
    pose = np.eye(4)
    pose[:3,:3] = [[0,-1,0],[1,0,0],[0,0,1]]
    pose[:3,3] = [1,2,3]
    np.testing.assert_allclose(camera_center(pose), [-2,1,-3])
    np.testing.assert_allclose(pose @ np.r_[camera_center(pose),1], [0,0,0,1])


def test_calibration_scales_principal_point_and_focal_length():
    settings=Settings.load()
    meta=metadata_from_probe(source(),settings)
    cam=CameraOptions(mode="calibrated",fx=1000,fy=1050,cx=959.5,cy=539.5,cols=1920,rows=1080,k1=.03)
    out=camera_config(cam,meta,settings)["Camera"]
    assert out["fx"] == pytest.approx(1000/3)
    assert out["cx"] == pytest.approx(319.5)
    assert out["k1"] == .03
    assert (out["cols"],out["rows"]) == (640,360)


def test_approximate_camera_uses_fov():
    settings=Settings.load()
    meta=metadata_from_probe(source(),settings)
    out=camera_config(CameraOptions(horizontal_fov=90),meta,settings)["Camera"]
    assert out["fx"] == pytest.approx(320)
    assert out["fy"] == out["fx"]


def test_rotated_dimensions_are_used_for_calibration():
    meta=metadata_from_probe(source(side_data_list=[{"rotation":-90}]),Settings.load())
    assert (meta["display_width"],meta["display_height"]) == (1080,1920)
    assert (meta["processing_width"],meta["processing_height"]) == (360,640)
    with pytest.raises(ValueError,match="orientation"):
        camera_config(CameraOptions(mode="calibrated",fx=900,fy=900,cx=960,cy=540,cols=1920,rows=1080),meta,Settings.load())


@pytest.mark.parametrize("updates",[{"duration":"nan"},{"duration":"1000"},{"avg_frame_rate":"0/0"}, {"codec_name":"unknown"},{"width":16000},{"sample_aspect_ratio":"2:1"}])
def test_rejects_invalid_metadata(updates):
    with pytest.raises(JobError):
        metadata_from_probe(source(**updates),Settings.load())


def test_never_upsamples_source_fps():
    assert metadata_from_probe(source(avg_frame_rate="10/1"),Settings.load(),30)["processed_fps"] == 10


def test_rejects_nan_intrinsics():
    with pytest.raises(ValueError):
        CameraOptions(horizontal_fov=math.nan)


def test_trajectory_rejects_wrong_quaternion_and_nonmonotonic_time(tmp_path):
    file=tmp_path/"trajectory.tum"
    file.write_text("0 1 2 3 0 0 0 0\n")
    with pytest.raises(ValueError,match="quaternion"): read_tum(file)
    file.write_text("1 1 2 3 0 0 0 1\n0 1 2 3 0 0 0 1\n")
    with pytest.raises(ValueError,match="timestamps"): read_tum(file)
