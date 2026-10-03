"""Detect active development environments (tmux, nix, direnv, venv)."""

from __future__ import annotations

import os

from session_context_command_runner import run_cmd


def _tmux_environment_value():
    code, session = run_cmd(["tmux", "display-message", "-p", "#S"])
    return session if code == 0 else "active"


def check_environment() -> dict:
    env = {}

    if os.environ.get("TMUX"):
        env["tmux"] = _tmux_environment_value()

    if os.environ.get("IN_NIX_SHELL"):
        env["nix_shell"] = os.environ.get("name", "active")

    if os.environ.get("DIRENV_DIR"):
        env["direnv"] = "active"

    if os.environ.get("VIRTUAL_ENV"):
        env["venv"] = os.path.basename(os.environ["VIRTUAL_ENV"])

    return env
