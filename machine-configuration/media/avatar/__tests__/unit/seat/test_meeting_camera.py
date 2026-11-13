import configparser
import json
from unittest.mock import Mock

import local_seat
import meeting_camera
import pytest

OBS_ARGUMENTS = [
    "--collection",
    "Avatar",
    "--profile",
    "Avatar",
    "--scene",
    "Avatar",
    "--startvirtualcam",
    "--disable-updater",
    "--disable-missing-files-check",
    "--multi",
]


@pytest.fixture
def obs(tmp_path, monkeypatch):
    home = tmp_path / "home"
    application = tmp_path / "OBS.app"
    application.mkdir()
    monkeypatch.setenv("HOME", str(home))
    monkeypatch.setattr(meeting_camera, "OBS_APPLICATION", application)
    calls = Mock()
    monkeypatch.setattr(local_seat, "end_processes_matching", calls.end)
    monkeypatch.setattr(meeting_camera.subprocess, "run", calls.run)
    return home, application, calls


def obs_support(home):
    return home / "Library/Application Support/obs-studio/basic"


def test_the_scene_collection_holds_one_browser_source_inside_one_scene():
    collection = meeting_camera.scene_collection()
    sources = {source["id"]: source for source in collection["sources"]}
    assert collection["name"] == "Avatar"
    assert collection["current_scene"] == "Avatar"
    assert collection["scene_order"] == [{"name": "Avatar"}]
    assert [source["id"] for source in collection["sources"]] == [
        "browser_source",
        "scene",
    ]
    browser = sources["browser_source"]
    assert browser["name"] == "Avatar"
    assert browser["settings"] == {
        "url": "http://localhost:8770/?viewer&bare",
        "width": 1280,
        "height": 720,
        "fps": 30,
        "fps_custom": True,
    }
    scene = sources["scene"]
    assert scene["name"] == "Avatar"
    assert [item["name"] for item in scene["settings"]["items"]] == ["Avatar"]


def test_the_profile_is_one_thousand_two_hundred_eighty_by_seven_hundred_twenty_at_thirty():
    profile = configparser.ConfigParser()
    profile.read_string(meeting_camera.profile_settings())
    assert profile["General"]["Name"] == "Avatar"
    assert dict(profile["Video"]) == {
        "basecx": "1280",
        "basecy": "720",
        "outputcx": "1280",
        "outputcy": "720",
        "fpstype": "0",
        "fpscommon": "30",
    }


def test_starting_writes_the_collection_and_the_profile_under_the_home(obs):
    home, _, _ = obs
    meeting_camera.start()
    written = json.loads((obs_support(home) / "scenes/Avatar.json").read_text())
    assert written == meeting_camera.scene_collection()
    profile = (obs_support(home) / "profiles/Avatar/basic.ini").read_text()
    assert profile == meeting_camera.profile_settings()


def test_starting_launches_a_separate_background_obs_with_the_virtual_camera(obs):
    _, _, calls = obs
    meeting_camera.start()
    launch = calls.run.call_args
    assert launch.args[0] == [
        "/usr/bin/open",
        "-g",
        "-n",
        "-a",
        "OBS",
        "--args",
        *OBS_ARGUMENTS,
    ]
    assert launch.kwargs["check"] is True
    assert launch.kwargs["timeout"] == local_seat.COMMAND_TIMEOUT_SECONDS


def test_starting_replaces_an_older_avatar_instance_before_launching(obs):
    _, _, calls = obs
    meeting_camera.start()
    assert [call[0] for call in calls.mock_calls] == ["end", "run"]
    assert calls.end.call_args.args == ("--collection Avatar",)


def test_stopping_ends_only_the_avatar_instance(obs):
    _, _, calls = obs
    meeting_camera.stop()
    calls.end.assert_called_once_with("--collection Avatar")
    calls.run.assert_not_called()


def test_a_missing_obs_is_a_clear_error_and_changes_nothing(obs):
    home, application, calls = obs
    application.rmdir()
    with pytest.raises(RuntimeError, match="OBS Studio is not installed") as refused:
        meeting_camera.start()
    assert str(application) in str(refused.value)
    assert not home.exists()
    assert calls.mock_calls == []


def test_the_real_obs_application_path_is_the_applications_folder():
    assert str(meeting_camera.OBS_APPLICATION) == "/Applications/OBS.app"
