import asyncio
import sys
from pathlib import Path

BRIDGE_PACKAGE_DIRECTORY_PATH = (
    Path(__file__).resolve().parents[2] / "scripts" / "cockpit_session_bridge"
)
sys.path.insert(0, str(BRIDGE_PACKAGE_DIRECTORY_PATH))

import cockpit_lifecycle_control
import cockpit_multiplexer_port
import cockpit_tmux_multiplexer

TMUX_EXECUTABLE_PATH = "/run/current-system/sw/bin/tmux"
COCKPIT_SOCKET_PREFIX = [TMUX_EXECUTABLE_PATH, "-L", "cockpit"]


class RecordingSubprocessRunner:
    def __init__(self, scripted_outputs=None):
        self.executed_commands = []
        self._scripted_outputs = scripted_outputs or {}

    async def __call__(self, multiplexer_command):
        self.executed_commands.append(multiplexer_command)
        for command_marker, output in self._scripted_outputs.items():
            if command_marker in multiplexer_command:
                return cockpit_multiplexer_port.CockpitMultiplexerCommandResult(
                    0, output, ""
                )
        return cockpit_multiplexer_port.CockpitMultiplexerCommandResult(0, "", "")


def build_tmux_multiplexer(subprocess_runner, socket_policy=None):
    return cockpit_tmux_multiplexer.CockpitTmuxMultiplexer(
        TMUX_EXECUTABLE_PATH,
        socket_policy or cockpit_lifecycle_control.CockpitTmuxSocketPolicy(),
        subprocess_runner=subprocess_runner,
    )


def dispatch_through_tmux(lifecycle_request, subprocess_runner, socket_policy=None):
    return asyncio.run(
        cockpit_lifecycle_control.dispatch_cockpit_lifecycle_request(
            build_tmux_multiplexer(subprocess_runner, socket_policy),
            lifecycle_request,
        )
    )
