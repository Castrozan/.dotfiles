import json
from types import SimpleNamespace
from unittest.mock import Mock

import pytest
from meetings import start


def test_virtual_only_preparation_never_attaches_a_physical_microphone(
    monkeypatch, capsys
):
    runner = Mock(return_value=SimpleNamespace(stdout="inactive\n", returncode=3))
    monkeypatch.setattr(start.subprocess, "run", runner)
    monkeypatch.setattr(start, "audio_ready", lambda: False)
    prepared = Mock()
    monkeypatch.setattr(start, "bring_up", prepared)
    start.main(virtual_only=True)
    prepared.assert_called_once_with(
        start.MEETING_TARGET, (start.renderer_ready, start.camera_ready)
    )
    assert all(call.args[0][0] != "avatar-audio" for call in runner.call_args_list)
    assert json.loads(capsys.readouterr().out)["physical_capture"] is False


@pytest.mark.parametrize("state", ["active", "activating", "reloading"])
def test_virtual_only_refuses_borrowed_runtime_without_changing_it(monkeypatch, state):
    runner = Mock(return_value=SimpleNamespace(stdout=state, returncode=0))
    monkeypatch.setattr(start.subprocess, "run", runner)
    prepared = Mock()
    monkeypatch.setattr(start, "bring_up", prepared)
    with pytest.raises(RuntimeError, match="left untouched"):
        start.main(virtual_only=True)
    prepared.assert_not_called()
    assert runner.call_count == 1
