import pytest
from orchestrator_cli.handover import cli as handover_cli
from release_test_support import ReleaseScenario


@pytest.fixture
def moved_panes(monkeypatch):
    moved = []

    def move(pane_id, label):
        moved.append((pane_id, label))
        return "wW:t9"

    monkeypatch.setattr(handover_cli, "move_pane_to_new_tab", move)
    return moved


@pytest.fixture
def scenario(monkeypatch, tmp_path, notifications, capsys, moved_panes):
    return ReleaseScenario(monkeypatch, tmp_path, notifications, capsys)
