import sys
from pathlib import Path

BRIDGE_PACKAGE_DIRECTORY_PATH = (
    Path(__file__).resolve().parents[2] / "scripts" / "cockpit_session_bridge"
)
sys.path.insert(0, str(BRIDGE_PACKAGE_DIRECTORY_PATH))

from cockpit_herdr_test_doubles import (
    HERDR_EXECUTABLE_PATH,
    HERDR_SESSION_PREFIX,
    ScriptedHerdrSubprocessRunner,
    dispatch_through_herdr as dispatch,
)


def test_list_sessions_reads_the_whole_inventory_from_one_snapshot_call():
    runner = ScriptedHerdrSubprocessRunner()

    response = dispatch({"operation": "list-sessions"}, runner)

    assert runner.executed_commands == [[*HERDR_SESSION_PREFIX, "api", "snapshot"]]
    assert response["sessions"][0] == {
        "sessionName": "dotfiles",
        "windows": [
            {
                "windowIdentifier": "w1T:tB",
                "windowTitle": "AIDP",
                "agentDriver": "claude",
            },
            {
                "windowIdentifier": "w1T:tF",
                "windowTitle": "hooks",
                "agentDriver": None,
            },
        ],
    }


def test_open_session_creates_an_unfocused_workspace_labelled_after_the_session():
    runner = ScriptedHerdrSubprocessRunner()

    dispatch({"operation": "open-session", "sessionName": "reports"}, runner)

    assert runner.executed_commands == [
        [
            *HERDR_SESSION_PREFIX,
            "workspace",
            "create",
            "--label",
            "reports",
            "--no-focus",
        ]
    ]


def test_close_session_resolves_the_workspace_identifier_from_its_label():
    runner = ScriptedHerdrSubprocessRunner()

    dispatch({"operation": "close-session", "sessionName": "clawde"}, runner)

    assert runner.mutation_commands == [
        [*HERDR_SESSION_PREFIX, "workspace", "close", "w1P"]
    ]


def test_rename_session_renames_the_resolved_workspace():
    runner = ScriptedHerdrSubprocessRunner()

    dispatch(
        {
            "operation": "rename-session",
            "currentSessionName": "dotfiles",
            "newSessionName": "dotfiles-review",
        },
        runner,
    )

    assert runner.mutation_commands == [
        [*HERDR_SESSION_PREFIX, "workspace", "rename", "w1T", "dotfiles-review"]
    ]


def test_a_session_name_with_no_matching_workspace_fails_instead_of_touching_another():
    runner = ScriptedHerdrSubprocessRunner()

    response = dispatch(
        {"operation": "close-session", "sessionName": "never-existed"}, runner
    )

    assert runner.mutation_commands == []
    assert response["exitCode"] == 1
    assert "never-existed" in response["standardError"]


def test_every_command_forwards_over_ssh_when_a_remote_host_is_configured():
    runner = ScriptedHerdrSubprocessRunner()

    dispatch(
        {"operation": "list-sessions"}, runner, remote_ssh_host="lucas.zanoni@kira"
    )

    executed_command = runner.executed_commands[0]
    assert executed_command[0] == "ssh"
    assert executed_command[-2] == "lucas.zanoni@kira"
    assert executed_command[-1] == "herdr --session default api snapshot"
    assert HERDR_EXECUTABLE_PATH not in executed_command[-1]
