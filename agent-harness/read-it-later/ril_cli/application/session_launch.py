from __future__ import annotations

import json
import os
import shlex
import socket
import subprocess
from dataclasses import dataclass, field

WORKING_STATE_TIMEOUT_MILLISECONDS = "180000"
BRIEF_DIRECTORY = "clawde/ril/briefs"
WORKSPACE_DIRECTORY_NAME = ".dotfiles"
MACHINE_NAME_VARIABLE = "RIL_MACHINE_NAME"
WRITE_FILE_SCRIPT = 'mkdir -p "$(dirname "$1")" && cat > "$1"'


class SessionLaunchFailed(RuntimeError):
    pass


def local_machine_name() -> str:
    return os.environ.get(MACHINE_NAME_VARIABLE) or socket.gethostname()


def run_command(arguments: list[str], standard_input: str | None = None) -> str:
    try:
        completed = subprocess.run(
            arguments,
            input=standard_input,
            capture_output=True,
            text=True,
            timeout=240,
            check=True,
        )
    except (OSError, subprocess.SubprocessError) as error:
        raise SessionLaunchFailed(f"{' '.join(arguments[:3])}: {error}") from error
    return completed.stdout


@dataclass(frozen=True)
class HerdrSessionLauncher:
    command_runner: object = run_command
    local_machine_name: str = field(default_factory=local_machine_name)

    def on_host(
        self, host: str, arguments: list[str], standard_input: str | None = None
    ) -> str:
        if host == self.local_machine_name:
            return self.command_runner(arguments, standard_input)
        return self.command_runner(["ssh", host, shlex.join(arguments)], standard_input)

    def home_directory(self, host: str) -> str:
        return self.on_host(host, ["sh", "-c", 'printf %s "$HOME"']).strip()

    def running_agent_names(self, host: str) -> set[str]:
        listing = json.loads(self.on_host(host, ["herdr", "agent", "list"]))
        return {
            str(agent.get("name"))
            for agent in listing["result"]["agents"]
            if agent.get("name")
        }

    def write_brief(self, host: str, brief_path: str, brief_text: str) -> None:
        self.on_host(
            host, ["sh", "-c", WRITE_FILE_SCRIPT, "sh", brief_path], brief_text
        )

    def start_claude(
        self, host: str, session_name: str, home: str, brief_path: str
    ) -> str:
        created = json.loads(
            self.on_host(
                host,
                [
                    "herdr",
                    "workspace",
                    "create",
                    "--label",
                    session_name,
                    "--cwd",
                    f"{home}/{WORKSPACE_DIRECTORY_NAME}",
                    "--no-focus",
                ],
            )
        )
        pane = created["result"]["root_pane"]["pane_id"]
        launch_line = shlex.join(["claude", f"Read {brief_path} and carry it out."])
        self.on_host(host, ["herdr", "pane", "run", pane, launch_line])
        self.on_host(host, ["herdr", "agent", "rename", pane, session_name])
        return pane

    def launch(self, host: str, session_name: str, brief_text: str) -> str:
        if session_name in self.running_agent_names(host):
            return "already-running"
        home = self.home_directory(host)
        brief_path = f"{home}/{BRIEF_DIRECTORY}/{session_name}.md"
        self.write_brief(host, brief_path, brief_text)
        pane = self.start_claude(host, session_name, home, brief_path)
        self.on_host(
            host,
            [
                "herdr",
                "agent",
                "wait",
                pane,
                "--until",
                "working",
                "--timeout",
                WORKING_STATE_TIMEOUT_MILLISECONDS,
            ],
        )
        return "launched"
