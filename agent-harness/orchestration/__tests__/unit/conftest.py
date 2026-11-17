import pytest
from orchestration_test_support import notifications as notifications
from orchestrator_cli.releases import released_sessions


@pytest.fixture(autouse=True)
def isolated_state_home(monkeypatch, tmp_path):
    monkeypatch.setenv("XDG_STATE_HOME", str(tmp_path / "state"))


@pytest.fixture(autouse=True)
def live_panes(monkeypatch):
    panes = {}
    monkeypatch.setattr(released_sessions, "live_pane", panes.get)
    return panes
