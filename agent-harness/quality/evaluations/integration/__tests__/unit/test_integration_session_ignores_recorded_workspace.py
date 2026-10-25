import os
import subprocess

import integration_session


def test_integration_session_never_follows_the_recorded_workspace_directory(
    monkeypatch, tmp_path
):
    recorded_environments = []

    def record_environment(command, **options):
        recorded_environments.append(options["env"])
        return subprocess.CompletedProcess(command, 0, "", "")

    monkeypatch.setattr(integration_session.subprocess, "run", record_environment)
    monkeypatch.setenv("CLAUDE_CODE_WORKSPACE_STATE_FILE", "/home/user/recorded")

    integration_session.run_claude_session("prompt", tmp_path)

    assert recorded_environments[0]["CLAUDE_CODE_WORKSPACE_STATE_FILE"] == os.devnull
