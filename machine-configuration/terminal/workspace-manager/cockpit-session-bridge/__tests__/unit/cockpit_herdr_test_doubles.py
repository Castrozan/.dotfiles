import asyncio
import json
import sys
from pathlib import Path

BRIDGE_PACKAGE_DIRECTORY_PATH = (
    Path(__file__).resolve().parents[2] / "scripts" / "cockpit_session_bridge"
)
sys.path.insert(0, str(BRIDGE_PACKAGE_DIRECTORY_PATH))

import cockpit_herdr_multiplexer
import cockpit_lifecycle_control
import cockpit_multiplexer_port

HERDR_EXECUTABLE_PATH = "/run/current-system/sw/bin/herdr"
HERDR_SESSION_PREFIX = [HERDR_EXECUTABLE_PATH, "--session", "default"]
RUNNING_HERDR_SERVER_STATUS_OUTPUT = (
    "status: running\nversion: 0.7.3\nprotocol: 16\ncompatible: yes\n"
)


def build_runtime_snapshot_output(workspaces, tabs, agents=(), panes=()):
    return json.dumps(
        {
            "id": "cli:api:snapshot",
            "result": {
                "snapshot": {
                    "workspaces": list(workspaces),
                    "tabs": list(tabs),
                    "agents": list(agents),
                    "panes": list(panes),
                }
            },
        }
    )


DOTFILES_SNAPSHOT_OUTPUT = build_runtime_snapshot_output(
    workspaces=[
        {"workspace_id": "w1T", "label": "dotfiles", "number": 7},
        {"workspace_id": "w1P", "label": "clawde", "number": 4},
    ],
    tabs=[
        {"tab_id": "w1T:tB", "workspace_id": "w1T", "label": "AIDP"},
        {"tab_id": "w1T:tF", "workspace_id": "w1T", "label": "hooks"},
        {"tab_id": "w1P:t3E", "workspace_id": "w1P", "label": "jenny"},
    ],
    agents=[
        {"tab_id": "w1T:tB", "agent": "claude"},
        {"tab_id": "w1P:t3E", "agent": "codex"},
    ],
    panes=[
        {
            "tab_id": "w1T:tB",
            "pane_id": "w1T:p1",
            "terminal_id": "term_6569e1e60304f89",
        },
        {
            "tab_id": "w1T:tF",
            "pane_id": "w1T:p2",
            "terminal_id": "term_656a545f71b2c8b",
        },
        {
            "tab_id": "w1P:t3E",
            "pane_id": "w1P:p3",
            "terminal_id": "term_6579e4e1e70b15ac",
        },
    ],
)


class ScriptedHerdrSubprocessRunner:
    def __init__(self, snapshot_output=DOTFILES_SNAPSHOT_OUTPUT):
        self.executed_commands = []
        self._snapshot_output = snapshot_output

    async def __call__(self, multiplexer_command):
        self.executed_commands.append(multiplexer_command)
        if _reads_the_runtime_snapshot(multiplexer_command):
            return cockpit_multiplexer_port.CockpitMultiplexerCommandResult(
                0, self._snapshot_output, ""
            )
        if "status" in " ".join(multiplexer_command):
            return cockpit_multiplexer_port.CockpitMultiplexerCommandResult(
                0, RUNNING_HERDR_SERVER_STATUS_OUTPUT, ""
            )
        return cockpit_multiplexer_port.CockpitMultiplexerCommandResult(0, "", "")

    @property
    def mutation_commands(self):
        return [
            executed_command
            for executed_command in self.executed_commands
            if not _reads_the_runtime_snapshot(executed_command)
        ]


def _reads_the_runtime_snapshot(multiplexer_command):
    return "snapshot" in " ".join(multiplexer_command)


def build_herdr_multiplexer(subprocess_runner, remote_ssh_host=""):
    return cockpit_herdr_multiplexer.CockpitHerdrMultiplexer(
        HERDR_EXECUTABLE_PATH,
        remote_ssh_host=remote_ssh_host,
        subprocess_runner=subprocess_runner,
    )


def dispatch_through_herdr(lifecycle_request, subprocess_runner, remote_ssh_host=""):
    return asyncio.run(
        cockpit_lifecycle_control.dispatch_cockpit_lifecycle_request(
            build_herdr_multiplexer(subprocess_runner, remote_ssh_host),
            lifecycle_request,
        )
    )
