import sys
from pathlib import Path

BRIDGE_PACKAGE_DIRECTORY_PATH = (
    Path(__file__).resolve().parents[2] / "scripts" / "cockpit_session_bridge"
)
sys.path.insert(0, str(BRIDGE_PACKAGE_DIRECTORY_PATH))

import pytest

from cockpit_herdr_test_doubles import (
    ScriptedHerdrSubprocessRunner,
    dispatch_through_herdr,
)
from cockpit_multiplexer_test_doubles import (
    RecordingSubprocessRunner,
    dispatch_through_tmux,
)

import cockpit_lifecycle_control

VIEW_STEERING_COMMAND_WORDS = ("focus", "select-window")


def executed_command_steers_a_view(executed_command):
    command_words = set(executed_command[-1].split()) | set(executed_command)
    return any(
        steering_word in command_words for steering_word in VIEW_STEERING_COMMAND_WORDS
    )


def test_no_herdr_lifecycle_operation_moves_another_client_view():
    runner = ScriptedHerdrSubprocessRunner()

    for lifecycle_request in (
        {"operation": "list-sessions"},
        {"operation": "open-session", "sessionName": "review"},
        {"operation": "close-session", "sessionName": "dotfiles"},
        {"operation": "open-window", "sessionName": "dotfiles", "windowTitle": "logs"},
        {"operation": "close-window", "windowIdentifier": "w1T:tF"},
    ):
        dispatch_through_herdr(lifecycle_request, runner)

    assert [
        executed_command
        for executed_command in runner.executed_commands
        if executed_command_steers_a_view(executed_command)
    ] == []


def test_no_tmux_lifecycle_operation_moves_another_client_view():
    runner = RecordingSubprocessRunner()

    for lifecycle_request in (
        {"operation": "list-sessions"},
        {"operation": "open-session", "sessionName": "review"},
        {"operation": "close-session", "sessionName": "dotfiles"},
        {"operation": "open-window", "sessionName": "dotfiles", "windowTitle": "logs"},
        {"operation": "close-window", "windowIdentifier": "@7"},
    ):
        dispatch_through_tmux(lifecycle_request, runner)

    assert [
        executed_command
        for executed_command in runner.executed_commands
        if executed_command_steers_a_view(executed_command)
    ] == []


def test_selecting_a_window_is_no_longer_a_lifecycle_operation():
    with pytest.raises(cockpit_lifecycle_control.UnsupportedCockpitLifecycleOperation):
        dispatch_through_herdr(
            {"operation": "select-window", "windowIdentifier": "w1P:t3E"},
            ScriptedHerdrSubprocessRunner(),
        )
