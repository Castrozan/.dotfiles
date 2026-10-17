import importlib.util
import json
from pathlib import Path
from unittest.mock import Mock

import pytest

specification = importlib.util.spec_from_file_location(
    "opencli_command", Path(__file__).resolve().parents[2] / "opencli_command.py"
)
module = importlib.util.module_from_spec(specification)
specification.loader.exec_module(module)


class Executed(BaseException):
    pass


@pytest.fixture
def command(tmp_path, monkeypatch):
    manifest = tmp_path / "manifest.json"
    manifest.write_text(
        json.dumps(
            [
                {"site": "hackernews", "name": "top", "browser": False},
                {"site": "web", "name": "read", "browser": True},
            ]
        )
    )
    for key, value in {
        "OPENCLI_MANIFEST": str(manifest),
        "OPENCLI_CLI": "/raw",
        "OPENCLI_JOB_RUNNER": "/job",
    }.items():
        monkeypatch.setenv(key, value)
    monkeypatch.delenv("OPENCLI_JOB_SCOPE", raising=False)
    execute = Mock(side_effect=Executed)
    monkeypatch.setattr(module.os, "execv", execute)
    return execute


@pytest.mark.parametrize(
    "arguments, expected",
    [
        (["hackernews", "top"], ["/raw", "hackernews", "top"]),
        (["list"], ["/raw", "list"]),
        (["web", "read", "--help"], ["/raw", "web", "read", "--help"]),
        (["web", "read"], ["/job", "--", "/raw", "web", "read"]),
        (
            ["web", "read", "--", "--help"],
            ["/job", "--", "/raw", "web", "read", "--", "--help"],
        ),
    ],
)
def test_commands_acquire_only_the_resources_they_need(
    command, monkeypatch, arguments, expected
):
    monkeypatch.setattr(module.sys, "argv", ["opencli", *arguments])
    with pytest.raises(Executed):
        module.main()
    assert command.call_args.args[1] == expected


def test_multistep_browser_requires_workflow_owner(command, monkeypatch):
    monkeypatch.setattr(
        module.sys, "argv", ["opencli", "browser", "open", "https://example.com"]
    )
    with pytest.raises(ValueError, match="opencli-run"):
        module.main()
    command.assert_not_called()


@pytest.mark.parametrize(
    "arguments",
    [["daemon", "restart"], ["daemon", "stop"], ["daemon", "restart", "--", "--help"]],
)
def test_callers_cannot_replace_or_stop_another_jobs_daemon(
    command, monkeypatch, arguments
):
    monkeypatch.setattr(module.sys, "argv", ["opencli", *arguments])
    with pytest.raises(ValueError, match="job owns its daemon"):
        module.main()
    command.assert_not_called()
