import json
import os
import subprocess
from types import SimpleNamespace
from unittest.mock import Mock

import pytest

import container_cleanup_watch
from container_cleanup_watch import ensure_cleanup_running, watch_cleanup


def test_cleanup_service_must_publish_readiness_before_work_starts(
    tmp_path, monkeypatch
):
    policy = SimpleNamespace(virtual_machine=True, state_root=str(tmp_path))
    monkeypatch.setattr(
        container_cleanup_watch,
        "run_command",
        Mock(return_value=SimpleNamespace(stdout=str(os.getpid()))),
    )
    monotonic = Mock(side_effect=[0, 0, 6])
    monkeypatch.setattr(container_cleanup_watch.time, "monotonic", monotonic)
    monkeypatch.setattr(container_cleanup_watch.time, "sleep", Mock())
    with pytest.raises(ValueError, match="did not become ready"):
        ensure_cleanup_running(policy)
    (tmp_path / "cleanup.json").write_text(
        json.dumps({"process_identifier": os.getpid()})
    )
    monotonic.side_effect = [0, 0]
    ensure_cleanup_running(policy)


def test_native_linux_uses_its_systemd_timer(monkeypatch):
    command = Mock()
    monkeypatch.setattr(container_cleanup_watch, "run_command", command)
    ensure_cleanup_running(SimpleNamespace(virtual_machine=False))
    command.assert_not_called()


def test_cleanup_watch_recovers_from_a_hung_cycle(tmp_path, monkeypatch):
    policy = SimpleNamespace(state_root=str(tmp_path))
    command = Mock(side_effect=[subprocess.TimeoutExpired("collect", 60), None])
    monkeypatch.setattr(container_cleanup_watch, "run_command", command)
    pause = Mock(side_effect=[None, KeyboardInterrupt])
    monkeypatch.setattr(container_cleanup_watch.time, "sleep", pause)
    with pytest.raises(KeyboardInterrupt):
        watch_cleanup(policy)
    assert command.call_count == 2
    assert (
        json.loads((tmp_path / "cleanup.json").read_text())["process_identifier"]
        == os.getpid()
    )
    assert [call.args[0] for call in pause.call_args_list] == [60, 60]
