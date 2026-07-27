import sys
from pathlib import Path

BRIDGE_PACKAGE_DIRECTORY_PATH = (
    Path(__file__).resolve().parents[2] / "scripts" / "cockpit_session_bridge"
)
sys.path.insert(0, str(BRIDGE_PACKAGE_DIRECTORY_PATH))

from cockpit_herdr_test_doubles import (
    HERDR_SESSION_PREFIX,
    ScriptedHerdrSubprocessRunner,
    dispatch_through_herdr as dispatch,
)


def test_open_window_with_an_agent_launch_command_starts_a_named_agent():
    runner = ScriptedHerdrSubprocessRunner()

    dispatch(
        {
            "operation": "open-window",
            "sessionName": "dotfiles",
            "windowTitle": "review",
            "agentLaunchCommand": "claude",
        },
        runner,
    )

    assert runner.mutation_commands == [
        [
            *HERDR_SESSION_PREFIX,
            "agent",
            "start",
            "review",
            "--workspace",
            "w1T",
            "--no-focus",
            "--",
            "/bin/sh",
            "-lc",
            "claude",
        ]
    ]


def test_open_window_without_a_launch_command_creates_a_plain_tab():
    runner = ScriptedHerdrSubprocessRunner()

    dispatch(
        {"operation": "open-window", "sessionName": "dotfiles", "windowTitle": "logs"},
        runner,
    )

    assert runner.mutation_commands == [
        [
            *HERDR_SESSION_PREFIX,
            "tab",
            "create",
            "--workspace",
            "w1T",
            "--label",
            "logs",
            "--no-focus",
        ]
    ]


def test_open_window_into_an_unknown_session_fails_without_creating_anything():
    runner = ScriptedHerdrSubprocessRunner()

    response = dispatch(
        {"operation": "open-window", "sessionName": "ghost", "windowTitle": "logs"},
        runner,
    )

    assert runner.mutation_commands == []
    assert response["exitCode"] == 1


def test_close_window_and_select_window_take_the_tab_identifier_straight_through():
    runner = ScriptedHerdrSubprocessRunner()

    dispatch({"operation": "close-window", "windowIdentifier": "w1T:tF"}, runner)
    dispatch({"operation": "select-window", "windowIdentifier": "w1P:t3E"}, runner)

    assert runner.mutation_commands == [
        [*HERDR_SESSION_PREFIX, "tab", "close", "w1T:tF"],
        [*HERDR_SESSION_PREFIX, "tab", "focus", "w1P:t3E"],
    ]
