import json
import sys

import pytest

import audio_cli
from pulse_audio_fake import Pulse, audio


@pytest.fixture
def pulse(monkeypatch):
    backend = Pulse()
    backend.sources.append({"name": "replacement.monitor"})
    monkeypatch.setattr(audio.pulse_audio, "run", backend.call)
    monkeypatch.setattr(audio.pulse_audio, "items", backend.items)
    return backend


@pytest.fixture
def runtime_directory(monkeypatch, tmp_path):
    monkeypatch.setenv("XDG_RUNTIME_DIR", str(tmp_path))
    return tmp_path / "avatar"


@pytest.fixture
def run_cli(monkeypatch, capsys):
    def run(*arguments):
        monkeypatch.setattr(sys, "argv", ["avatar-audio", *arguments])
        audio_cli.main()
        return json.loads(capsys.readouterr().out)

    return run


def microphone_loopback(pulse):
    return next(
        module
        for module in pulse.modules
        if module["name"] == "module-loopback"
        and "sink=AvatarHuman" in module["argument"]
    )


def core_module(pulse, sink_name):
    return next(
        module
        for module in pulse.modules
        if module["argument"].startswith(f"sink_name={sink_name} ")
    )


def test_vanished_microphone_leaves_the_graph_running_and_detached(
    pulse, run_cli, runtime_directory
):
    run_cli("start")
    run_cli("open")
    pulse.modules.remove(microphone_loopback(pulse))
    status = run_cli("status")
    assert status["running"] is True
    assert status["phase"] == "running-detached"
    assert status["microphone"] is None


def test_open_after_a_vanished_microphone_attaches_the_default_source_again(
    pulse, run_cli, runtime_directory
):
    run_cli("start")
    run_cli("open")
    pulse.modules.remove(microphone_loopback(pulse))
    pulse.default_source = "replacement.monitor"
    status = run_cli("open")
    assert status["microphone"] == "replacement.monitor"
    assert "source=replacement.monitor" in microphone_loopback(pulse)["argument"]


def test_stop_unloads_the_microphone_loopback_and_every_core_module(
    pulse, run_cli, runtime_directory
):
    run_cli("start")
    run_cli("open")
    stopped = run_cli("stop")
    assert pulse.modules == [{"index": 1, "name": "unrelated", "argument": "keep"}]
    assert stopped["phase"] == "absent"
    assert stopped["microphone"] is None


def test_attach_refuses_while_a_live_microphone_is_attached(
    pulse, run_cli, runtime_directory
):
    run_cli("start")
    run_cli("open")
    with pytest.raises(ValueError, match="already attached"):
        run_cli("attach", "replacement.monitor")


def test_vanished_core_module_reports_orphaned_and_not_running(
    pulse, run_cli, runtime_directory
):
    run_cli("start")
    pulse.modules.remove(core_module(pulse, "AvatarMix"))
    status = run_cli("status")
    assert status["running"] is False
    assert status["phase"] == "orphaned"
