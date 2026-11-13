import configparser
import json
import types
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
    "--disable-updater",
    "--disable-missing-files-check",
    "--disable-shutdown-check",
    "--multi",
]


class Clock:
    def __init__(self):
        self.now = 0.0

    def monotonic(self):
        return self.now

    def sleep(self, seconds):
        self.now += seconds


@pytest.fixture
def obs(tmp_path, monkeypatch):
    home = tmp_path / "home"
    application = tmp_path / "OBS.app"
    application.mkdir()
    monkeypatch.setenv("HOME", str(home))
    monkeypatch.setattr(meeting_camera, "OBS_APPLICATION", application)
    monkeypatch.setattr(meeting_camera, "time", Clock())
    calls = Mock()
    calls.run.side_effect = lambda *_, **__: camera_report(home).write_text("active")
    monkeypatch.setattr(local_seat, "end_processes_matching", calls.end)
    monkeypatch.setattr(meeting_camera.subprocess, "run", calls.run)
    return types.SimpleNamespace(home=home, application=application, calls=calls)


def obs_support(home):
    return home / "Library/Application Support/obs-studio/basic"


def camera_report(home):
    return home / ".local/share/avatar/virtual-camera-report"


def test_the_scene_collection_holds_one_browser_source_inside_one_scene():
    collection = meeting_camera.scene_collection()
    sources = {source["id"]: source for source in collection["sources"]}
    assert collection["name"] == "Avatar"
    assert collection["current_scene"] == "Avatar"
    assert collection["scene_order"] == [{"name": "Avatar"}]
    assert list(sources) == ["browser_source", "scene"]
    assert sources["browser_source"]["settings"] == {
        "url": "http://localhost:8770/?viewer&bare",
        "width": 1280,
        "height": 720,
        "fps": 30,
        "fps_custom": True,
    }
    items = sources["scene"]["settings"]["items"]
    assert [item["name"] for item in items] == [sources["browser_source"]["name"]]


def test_the_scene_and_its_source_never_share_a_name():
    names = [source["name"] for source in meeting_camera.scene_collection()["sources"]]
    assert sorted(names) == ["Avatar", "Avatar View"]


def test_the_collection_loads_the_script_that_starts_the_camera(obs):
    [script] = meeting_camera.scene_collection()["modules"]["scripts-tool"]
    assert script["path"] == str(meeting_camera.CAMERA_START_SCRIPT)
    assert meeting_camera.CAMERA_START_SCRIPT.name == "start_virtual_camera.lua"
    assert "obs_frontend_start_virtualcam" in (
        meeting_camera.CAMERA_START_SCRIPT.read_text()
    )
    assert script["settings"] == {"report_path": str(camera_report(obs.home))}


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
    meeting_camera.start()
    written = json.loads((obs_support(obs.home) / "scenes/Avatar.json").read_text())
    assert written == meeting_camera.scene_collection()
    profile = (obs_support(obs.home) / "profiles/Avatar/basic.ini").read_text()
    assert profile == meeting_camera.profile_settings()


def test_starting_launches_a_separate_background_obs_that_survives_an_unclean_end(obs):
    meeting_camera.start()
    launch = obs.calls.run.call_args
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
    meeting_camera.start()
    assert [call[0] for call in obs.calls.mock_calls] == ["end", "run"]


def test_stopping_ends_only_the_avatar_instance_without_asking_it(obs):
    meeting_camera.stop()
    obs.calls.end.assert_called_once_with("--collection Avatar", "KILL")
    obs.calls.run.assert_not_called()


@pytest.mark.parametrize("reported", ["inactive", None])
def test_a_camera_that_does_not_run_is_a_failure_naming_the_approval(obs, reported):
    def launch(*_, **__):
        if reported:
            camera_report(obs.home).write_text(reported)

    obs.calls.run.side_effect = launch
    with pytest.raises(RuntimeError, match="Camera Extensions"):
        meeting_camera.start()


def test_a_report_left_by_an_earlier_start_is_not_believed(obs):
    camera_report(obs.home).parent.mkdir(parents=True)
    camera_report(obs.home).write_text("active")
    obs.calls.run.side_effect = None
    with pytest.raises(RuntimeError, match="did not start its virtual camera"):
        meeting_camera.start()


def test_waiting_for_the_report_is_bounded(obs):
    obs.calls.run.side_effect = None
    with pytest.raises(RuntimeError):
        meeting_camera.start()
    waited = meeting_camera.time.monotonic()
    assert meeting_camera.CAMERA_REPORT_WAIT_SECONDS <= waited
    assert waited <= meeting_camera.CAMERA_REPORT_WAIT_SECONDS + local_seat.POLL_SECONDS


def test_a_missing_obs_is_a_clear_error_and_changes_nothing(obs):
    obs.application.rmdir()
    with pytest.raises(RuntimeError, match="OBS Studio is not installed") as refused:
        meeting_camera.start()
    assert str(obs.application) in str(refused.value)
    assert not obs.home.exists()
    assert obs.calls.mock_calls == []


def test_the_real_obs_application_path_is_the_applications_folder():
    assert str(meeting_camera.OBS_APPLICATION) == "/Applications/OBS.app"


@pytest.mark.parametrize(
    ("arguments", "signal_flag"),
    [(("--collection Avatar",), "-TERM"), (("--collection Avatar", "KILL"), "-KILL")],
)
def test_ending_processes_sends_the_named_signal(monkeypatch, arguments, signal_flag):
    run = Mock()
    monkeypatch.setattr(local_seat.subprocess, "run", run)
    local_seat.end_processes_matching(*arguments)
    assert run.call_args.args[0] == [
        "/usr/bin/pkill",
        signal_flag,
        "-f",
        "--",
        "--collection Avatar",
    ]
    assert run.call_args.kwargs["timeout"] == local_seat.COMMAND_TIMEOUT_SECONDS
