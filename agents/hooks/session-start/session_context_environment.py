"""Detect active development environments (tmux, nix, direnv, venv)."""

import os

from session_context_command_runner import run_cmd


def check_environment() -> dict:
    env = {}

    if os.environ.get("TMUX"):
        code, session = run_cmd(["tmux", "display-message", "-p", "#S"])
        env["tmux"] = session if code == 0 else "active"

    if os.environ.get("IN_NIX_SHELL"):
        env["nix_shell"] = os.environ.get("name", "active")

    if os.environ.get("DIRENV_DIR"):
        env["direnv"] = "active"

    if os.environ.get("VIRTUAL_ENV"):
        env["venv"] = os.path.basename(os.environ["VIRTUAL_ENV"])

    return env
