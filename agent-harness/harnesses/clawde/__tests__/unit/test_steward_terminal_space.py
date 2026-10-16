import os
import subprocess
from unittest.mock import Mock

import pytest

import steward_terminal_space


@pytest.mark.parametrize("rows", [8, 38])
def test_drawable_terminal_preserves_layout(monkeypatch, rows):
    monkeypatch.setattr(os, "get_terminal_size", lambda: os.terminal_size((132, rows)))
    run = Mock()
    monkeypatch.setattr(subprocess, "run", run)

    steward_terminal_space.ensure_terminal_space()

    run.assert_not_called()


def test_collapsed_terminal_zooms_only_its_own_pane(monkeypatch):
    sizes = iter([os.terminal_size((132, 2)), os.terminal_size((132, 38))])
    monkeypatch.setattr(os, "get_terminal_size", lambda: next(sizes))
    monkeypatch.setenv("HERDR_PANE_ID", "w2B:pA")
    run = Mock()
    monkeypatch.setattr(subprocess, "run", run)

    steward_terminal_space.ensure_terminal_space()

    run.assert_called_once_with(
        ["herdr", "pane", "zoom", "w2B:pA", "--on"],
        check=True,
        capture_output=True,
        text=True,
        timeout=5,
    )


def test_collapsed_terminal_requires_its_pane_identity(monkeypatch):
    monkeypatch.setattr(os, "get_terminal_size", lambda: os.terminal_size((132, 2)))
    monkeypatch.delenv("HERDR_PANE_ID", raising=False)
    run = Mock()
    monkeypatch.setattr(subprocess, "run", run)

    with pytest.raises(SystemExit, match="HERDR_PANE_ID"):
        steward_terminal_space.ensure_terminal_space()

    run.assert_not_called()


def test_zoom_failure_prevents_launch(monkeypatch):
    monkeypatch.setattr(os, "get_terminal_size", lambda: os.terminal_size((132, 2)))
    monkeypatch.setenv("HERDR_PANE_ID", "w2B:pA")
    monkeypatch.setattr(
        subprocess,
        "run",
        Mock(side_effect=subprocess.TimeoutExpired("herdr", 5)),
    )

    with pytest.raises(subprocess.TimeoutExpired):
        steward_terminal_space.ensure_terminal_space()


def test_zoom_must_restore_drawable_terminal(monkeypatch):
    monkeypatch.setattr(os, "get_terminal_size", lambda: os.terminal_size((132, 2)))
    monkeypatch.setenv("HERDR_PANE_ID", "w2B:pA")
    monkeypatch.setattr(subprocess, "run", Mock())

    with pytest.raises(SystemExit, match="fewer than 8 rows"):
        steward_terminal_space.ensure_terminal_space()
