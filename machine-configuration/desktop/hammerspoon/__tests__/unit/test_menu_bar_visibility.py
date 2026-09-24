import importlib.util
import signal
from pathlib import Path
from unittest.mock import Mock

import pytest


@pytest.fixture
def reveal_module(monkeypatch):
    script = Path(__file__).parents[2] / "scripts" / "reveal-menu-bar.py"
    specification = importlib.util.spec_from_file_location(
        "menu_bar_visibility", script
    )
    module = importlib.util.module_from_spec(specification)
    specification.loader.exec_module(module)
    monkeypatch.setattr(module.signal, "signal", Mock())
    return module


def configure_visibility(reveal_module, monkeypatch, results=(0, 0)):
    library = Mock()
    library.SLSMainConnectionID.return_value = 42
    library.SLSSetMenuBarVisibilityOverrideOnDisplay.side_effect = results
    cancellation = Mock()
    cancellation.is_set.return_value = False
    monkeypatch.setattr(reveal_module.ctypes, "CDLL", Mock(return_value=library))
    monkeypatch.setattr(
        reveal_module.threading, "Event", Mock(return_value=cancellation)
    )
    return library.SLSSetMenuBarVisibilityOverrideOnDisplay, cancellation


def test_reveal_is_display_scoped_and_releases_after_one_second(
    reveal_module, monkeypatch
):
    visibility, cancellation = configure_visibility(reveal_module, monkeypatch)

    reveal_module.reveal_menu_bar(7)

    assert [call.args for call in visibility.call_args_list] == [
        (42, 7, True),
        (42, 7, False),
    ]
    cancellation.wait.assert_called_once_with(1)


def test_termination_interrupts_the_wait_and_releases_visibility(
    reveal_module, monkeypatch
):
    visibility, cancellation = configure_visibility(reveal_module, monkeypatch)

    def terminate_during_wait(_duration):
        for arguments, _keywords in reveal_module.signal.signal.call_args_list:
            if arguments[0] == signal.SIGTERM:
                arguments[1](signal.SIGTERM, None)

    cancellation.wait.side_effect = terminate_during_wait
    reveal_module.reveal_menu_bar(7)

    cancellation.set.assert_called_once_with()
    assert visibility.call_args_list[-1].args == (42, 7, False)


def test_cancellation_before_reveal_leaves_visibility_untouched(
    reveal_module, monkeypatch
):
    visibility, cancellation = configure_visibility(reveal_module, monkeypatch)
    cancellation.is_set.return_value = True

    reveal_module.reveal_menu_bar(7)

    visibility.assert_not_called()


def test_wait_failure_still_releases_visibility(reveal_module, monkeypatch):
    visibility, cancellation = configure_visibility(reveal_module, monkeypatch)
    cancellation.wait.side_effect = RuntimeError("interrupted")

    with pytest.raises(RuntimeError, match="interrupted"):
        reveal_module.reveal_menu_bar(7)

    assert visibility.call_args_list[-1].args == (42, 7, False)


def test_rejected_reveal_does_not_wait_or_change_visibility_again(
    reveal_module, monkeypatch
):
    visibility, cancellation = configure_visibility(reveal_module, monkeypatch, (1001,))

    with pytest.raises(RuntimeError, match="reveal failed: 1001"):
        reveal_module.reveal_menu_bar(7)

    visibility.assert_called_once_with(42, 7, True)
    cancellation.wait.assert_not_called()


def test_release_failure_is_reported(reveal_module, monkeypatch):
    configure_visibility(reveal_module, monkeypatch, (0, 1002))

    with pytest.raises(RuntimeError, match="release failed: 1002"):
        reveal_module.reveal_menu_bar(7)
