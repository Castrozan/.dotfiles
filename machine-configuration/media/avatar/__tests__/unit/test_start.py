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
