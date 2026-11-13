from unittest.mock import Mock

import install_call_audio_drivers
import pytest


def packaged_driver(directory, name, body):
    driver = directory / "store" / name
    (driver / "Contents").mkdir(parents=True)
    (driver / "Contents" / "driver").write_text(body)
    return driver


@pytest.fixture
def audio_server(tmp_path, monkeypatch):
    monkeypatch.setattr(
        install_call_audio_drivers, "DRIVER_DIRECTORY", tmp_path / "HAL"
    )
    restarted = Mock()
    monkeypatch.setattr(install_call_audio_drivers, "restart_audio_server", restarted)
    return restarted


def run_installer(monkeypatch, *drivers):
    monkeypatch.setattr(
        install_call_audio_drivers.sys, "argv", ["install", *map(str, drivers)]
    )
    install_call_audio_drivers.main()


def test_missing_drivers_are_installed_and_the_audio_server_restarts_once(
    tmp_path, monkeypatch, audio_server
):
    microphone = packaged_driver(tmp_path, "BlackHole2ch.driver", "two")
    speaker = packaged_driver(tmp_path, "BlackHole16ch.driver", "sixteen")
    run_installer(monkeypatch, microphone, speaker)
    installed = tmp_path / "HAL"
    assert (installed / "BlackHole2ch.driver/Contents/driver").read_text() == "two"
    assert (installed / "BlackHole16ch.driver/Contents/driver").read_text() == "sixteen"
    audio_server.assert_called_once_with()


def test_drivers_already_in_place_leave_the_audio_server_alone(
    tmp_path, monkeypatch, audio_server
):
    microphone = packaged_driver(tmp_path, "BlackHole2ch.driver", "two")
    run_installer(monkeypatch, microphone)
    audio_server.reset_mock()
    run_installer(monkeypatch, microphone)
    audio_server.assert_not_called()


def test_a_changed_driver_replaces_the_installed_one(
    tmp_path, monkeypatch, audio_server
):
    run_installer(monkeypatch, packaged_driver(tmp_path, "BlackHole2ch.driver", "old"))
    (tmp_path / "store/BlackHole2ch.driver/Contents/driver").write_text("new")
    (tmp_path / "HAL/BlackHole2ch.driver/Contents/stale").write_text("left over")
    run_installer(monkeypatch, tmp_path / "store/BlackHole2ch.driver")
    contents = tmp_path / "HAL/BlackHole2ch.driver/Contents"
    assert (contents / "driver").read_text() == "new"
    assert not (contents / "stale").exists()
    assert audio_server.call_count == 2
