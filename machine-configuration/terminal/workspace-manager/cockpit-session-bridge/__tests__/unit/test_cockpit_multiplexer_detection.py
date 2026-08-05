import asyncio
import sys
from pathlib import Path

BRIDGE_PACKAGE_DIRECTORY_PATH = (
    Path(__file__).resolve().parents[2] / "scripts" / "cockpit_session_bridge"
)
sys.path.insert(0, str(BRIDGE_PACKAGE_DIRECTORY_PATH))

import cockpit_lifecycle_control
import cockpit_multiplexer_detection
import cockpit_multiplexer_port
import settings as bridge_settings
from cockpit_herdr_test_doubles import (
    HERDR_EXECUTABLE_PATH,
    RUNNING_HERDR_SERVER_STATUS_OUTPUT,
)
from cockpit_multiplexer_test_doubles import TMUX_EXECUTABLE_PATH

DETECTION_SETTINGS = bridge_settings.CockpitSessionBridgeSettings(
    listen_address="127.0.0.1",
    listen_port=8787,
    session_command=["/bin/sh", "-il"],
    allowed_request_origin="https://lucaszanoni.com",
    terminal_type="xterm-256color",
    cockpit_tmux_executable_path=TMUX_EXECUTABLE_PATH,
    cockpit_herdr_executable_path=HERDR_EXECUTABLE_PATH,
)


class ProbeAnsweringSubprocessRunner:
    def __init__(self, *, herdr_answer=None, tmux_answer=None):
        self.probed_commands = []
        self._herdr_answer = herdr_answer
        self._tmux_answer = tmux_answer

    async def __call__(self, multiplexer_command):
        self.probed_commands.append(multiplexer_command)
        answer = (
            self._herdr_answer
            if HERDR_EXECUTABLE_PATH in multiplexer_command
            else self._tmux_answer
        )
        if answer is None:
            raise OSError("no such executable")
        return answer


def detect(subprocess_runner):
    return asyncio.run(
        cockpit_multiplexer_detection.detect_cockpit_multiplexer(
            DETECTION_SETTINGS,
            cockpit_lifecycle_control.CockpitTmuxSocketPolicy(),
            subprocess_runner=subprocess_runner,
        )
    ).multiplexer_name


def answered(exit_code, standard_output=""):
    return cockpit_multiplexer_port.CockpitMultiplexerCommandResult(
        exit_code, standard_output, ""
    )


def test_a_running_herdr_server_wins_before_tmux_is_ever_probed():
    runner = ProbeAnsweringSubprocessRunner(
        herdr_answer=answered(0, RUNNING_HERDR_SERVER_STATUS_OUTPUT),
        tmux_answer=answered(0, "dotfiles\n"),
    )

    assert detect(runner) == "herdr"
    assert len(runner.probed_commands) == 1


def test_a_live_tmux_server_wins_when_the_herdr_server_is_down():
    runner = ProbeAnsweringSubprocessRunner(
        herdr_answer=answered(1, "status: not running\n"),
        tmux_answer=answered(0, "dotfiles\n"),
    )

    assert detect(runner) == "tmux"


def test_herdr_wins_when_neither_server_answers_but_herdr_is_installed():
    runner = ProbeAnsweringSubprocessRunner(
        herdr_answer=answered(1, "status: not running\n"),
        tmux_answer=answered(1, "no server running on /private/tmp/tmux-503/default"),
    )

    assert detect(runner) == "herdr"


def test_tmux_wins_when_the_herdr_executable_is_missing_entirely():
    runner = ProbeAnsweringSubprocessRunner(
        herdr_answer=None,
        tmux_answer=answered(1, "no server running on /private/tmp/tmux-503/default"),
    )

    assert detect(runner) == "tmux"


def test_a_missing_tmux_executable_never_breaks_detection():
    runner = ProbeAnsweringSubprocessRunner(
        herdr_answer=answered(1, "status: not running\n"), tmux_answer=None
    )

    assert detect(runner) == "herdr"


def test_the_herdr_probe_asks_the_server_for_its_status_without_a_session():
    runner = ProbeAnsweringSubprocessRunner(
        herdr_answer=answered(0, RUNNING_HERDR_SERVER_STATUS_OUTPUT)
    )

    detect(runner)

    assert runner.probed_commands == [[HERDR_EXECUTABLE_PATH, "status", "server"]]
