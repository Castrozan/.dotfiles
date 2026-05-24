import importlib
import json
import os
import sys
from unittest.mock import MagicMock

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))

glab_harness = importlib.import_module("glab-harness")


@pytest.fixture(autouse=True)
def set_gitlab_token_environment_variable(monkeypatch):
    monkeypatch.setenv("GITLAB_TOKEN", "fake-token-for-testing")
    monkeypatch.setenv("GITLAB_COM_TOKEN", "fake-com-token-for-testing")


@pytest.fixture(autouse=True)
def mock_git_remote(monkeypatch):
    import subprocess

    original_run = subprocess.run

    def patched_run(command, **kwargs):
        if isinstance(command, list) and "get-url" in command:
            return subprocess.CompletedProcess(
                args=command,
                returncode=0,
                stdout="git@git.coates.io:digital-production/mcdca-tools/mcdca-workspace.git\n",
                stderr="",
            )
        return original_run(command, **kwargs)

    monkeypatch.setattr(subprocess, "run", patched_run)


@pytest.fixture
def glab_harness_module():
    return glab_harness


@pytest.fixture
def make_mock_http_response():
    def _build(response_data):
        response_body = json.dumps(response_data).encode("utf-8")
        mock_response = MagicMock()
        mock_response.read.return_value = response_body
        mock_response.__enter__ = lambda s: s
        mock_response.__exit__ = MagicMock(return_value=False)
        return mock_response

    return _build
