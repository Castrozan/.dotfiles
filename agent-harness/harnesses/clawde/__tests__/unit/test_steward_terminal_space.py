import os
import termios
from unittest.mock import Mock

import pytest

import steward_terminal_space


@pytest.mark.parametrize("rows", [8, 38])
def test_drawable_terminal_preserves_layout(monkeypatch, rows):
    monkeypatch.setattr(os, "get_terminal_size", lambda: os.terminal_size((132, rows)))
    resize = Mock()
    monkeypatch.setattr(termios, "tcsetwinsize", resize)

    steward_terminal_space.ensure_terminal_space()

    resize.assert_not_called()


@pytest.mark.parametrize("columns, rows", [(132, 2), (80, 0), (24, 7)])
def test_collapsed_terminal_resizes_only_its_inherited_terminal(
    monkeypatch, columns, rows
):
    monkeypatch.setattr(
        os, "get_terminal_size", lambda: os.terminal_size((columns, rows))
    )
    resize = Mock()
    monkeypatch.setattr(termios, "tcsetwinsize", resize)

    steward_terminal_space.ensure_terminal_space()

    resize.assert_called_once_with(1, (8, columns))


def test_nonterminal_output_prevents_launch(monkeypatch):
    monkeypatch.setattr(
        os, "get_terminal_size", Mock(side_effect=OSError("no terminal"))
    )
    resize = Mock()
    monkeypatch.setattr(termios, "tcsetwinsize", resize)

    with pytest.raises(OSError, match="no terminal"):
        steward_terminal_space.ensure_terminal_space()

    resize.assert_not_called()


def test_resize_failure_prevents_launch(monkeypatch):
    monkeypatch.setattr(os, "get_terminal_size", lambda: os.terminal_size((132, 2)))
    monkeypatch.setattr(
        termios,
        "tcsetwinsize",
        Mock(side_effect=OSError("resize denied")),
    )

    with pytest.raises(OSError, match="resize denied"):
        steward_terminal_space.ensure_terminal_space()
