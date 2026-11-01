import importlib.util
import json
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock


spec = importlib.util.spec_from_file_location(
    "avatar_start", Path(__file__).resolve().parents[2] / "scripts/start.py"
)
start = importlib.util.module_from_spec(spec)
spec.loader.exec_module(start)


def test_start_recovers_a_missing_graph_before_claiming_readiness(monkeypatch):
    runner = Mock()
    monkeypatch.setattr(start.subprocess, "run", runner)
    monkeypatch.setattr(start, "audio_ready", Mock(side_effect=[False, True]))
    monkeypatch.setattr(start, "wait_until_ready", Mock())
    start.main()
    assert [call.args[0] for call in runner.call_args_list] == [
        ["systemctl", "--user", "stop", "avatar.target"],
        ["systemctl", "--user", "start", "avatar.target"],
    ]


def test_healthy_start_preserves_the_running_runtime(monkeypatch):
    runner = Mock()
    monkeypatch.setattr(start.subprocess, "run", runner)
    monkeypatch.setattr(start, "audio_ready", Mock(return_value=True))
    monkeypatch.setattr(start, "wait_until_ready", Mock())
    start.main()
    runner.assert_called_once_with(
        ["systemctl", "--user", "start", "avatar.target"], check=True
    )


def test_a_target_is_ready_only_when_all_of_its_own_checks_pass(monkeypatch):
    monkeypatch.setattr(start, "service_failed", lambda: False)
    monkeypatch.setattr(start.time, "sleep", Mock())
    answers = iter([False, True])
    start.wait_until_ready((lambda: next(answers), lambda: True))


def test_a_failed_bring_up_stops_only_the_requested_target(monkeypatch):
    runner = Mock()
    monkeypatch.setattr(start.subprocess, "run", runner)
    monkeypatch.setattr(start, "audio_ready", Mock(return_value=True))
    monkeypatch.setattr(start, "wait_until_ready", Mock(side_effect=TimeoutError))
    try:
        start.bring_up("avatar-conversation.target", ())
    except TimeoutError:
        pass
    assert runner.call_args_list[-1].args[0] == [
        "systemctl",
        "--user",
        "stop",
        "avatar-conversation.target",
    ]


def test_audio_readiness_requires_a_running_owned_graph(monkeypatch):
    runner = Mock(
        return_value=SimpleNamespace(
            returncode=0, stdout=json.dumps({"running": False})
        )
    )
    monkeypatch.setattr(start.subprocess, "run", runner)
    assert start.audio_ready() is False
    runner.return_value = SimpleNamespace(
        returncode=0, stdout=json.dumps({"running": True})
    )
    assert start.audio_ready() is True
