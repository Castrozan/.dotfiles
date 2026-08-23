import json
import subprocess
from pathlib import Path

import pytest

import run_dotfiles_workflow


def completed_workflow(stdout: str, stderr: str = "") -> subprocess.CompletedProcess:
    return subprocess.CompletedProcess(
        args=["claude"], returncode=0, stdout=stdout, stderr=stderr
    )


def test_workflow_name_comes_from_the_packaged_command(monkeypatch):
    monkeypatch.setenv(
        run_dotfiles_workflow.WORKFLOW_NAME_VARIABLE, "dotfiles-housekeeping"
    )

    assert run_dotfiles_workflow.resolve_workflow_name() == "dotfiles-housekeeping"


def test_running_the_script_directly_names_the_packaged_command(monkeypatch):
    monkeypatch.delenv(run_dotfiles_workflow.WORKFLOW_NAME_VARIABLE, raising=False)

    with pytest.raises(SystemExit) as failure:
        run_dotfiles_workflow.resolve_workflow_name()

    assert "dotfiles-*" in str(failure.value)


def test_help_is_titled_with_the_packaged_command(capsys):
    with pytest.raises(SystemExit):
        run_dotfiles_workflow.parse_command_line("dotfiles-change-review", ["--help"])

    assert "usage: dotfiles-change-review" in capsys.readouterr().out


def test_slash_command_carries_the_resolved_root():
    slash_command = run_dotfiles_workflow.build_slash_command(
        "dotfiles-change-review", Path("/checkouts/dotfiles"), ""
    )

    assert slash_command == ('/dotfiles-change-review {"root": "/checkouts/dotfiles"}')


def test_slash_command_carries_the_review_scope_when_given():
    slash_command = run_dotfiles_workflow.build_slash_command(
        "dotfiles-change-review", Path("/checkouts/dotfiles"), "origin/main..HEAD"
    )

    assert json.loads(slash_command.split(" ", 1)[1]) == {
        "root": "/checkouts/dotfiles",
        "ref": "origin/main..HEAD",
    }


def test_root_defaults_to_the_checkout_of_the_current_directory(monkeypatch):
    monkeypatch.setattr(
        run_dotfiles_workflow.subprocess,
        "run",
        lambda *_, **__: subprocess.CompletedProcess(
            args=["git"], returncode=0, stdout="/checkouts/dotfiles\n", stderr=""
        ),
    )

    assert run_dotfiles_workflow.resolve_repository_root("") == Path(
        "/checkouts/dotfiles"
    )


def test_root_outside_a_checkout_fails_with_the_flag_to_pass(monkeypatch):
    monkeypatch.setattr(
        run_dotfiles_workflow.subprocess,
        "run",
        lambda *_, **__: subprocess.CompletedProcess(
            args=["git"], returncode=128, stdout="", stderr="not a git repository"
        ),
    )

    with pytest.raises(SystemExit) as failure:
        run_dotfiles_workflow.resolve_repository_root("")

    assert "--root" in str(failure.value)


def test_report_is_the_result_the_envelope_carries():
    report = run_dotfiles_workflow.extract_report(
        completed_workflow(json.dumps({"is_error": False, "result": "# Findings\n"}))
    )

    assert report == "# Findings\n"


def test_failed_workflow_reports_its_own_error():
    with pytest.raises(SystemExit) as failure:
        run_dotfiles_workflow.extract_report(
            completed_workflow(
                json.dumps(
                    {
                        "is_error": True,
                        "result": "",
                        "subtype": "error_during_execution",
                    }
                )
            )
        )

    assert "error_during_execution" in str(failure.value)


def test_unparseable_output_surfaces_the_raw_failure():
    with pytest.raises(SystemExit) as failure:
        run_dotfiles_workflow.extract_report(
            completed_workflow("", stderr="claude: not logged in")
        )

    assert "not logged in" in str(failure.value)


def test_missing_claude_asks_for_the_rebuild(monkeypatch):
    monkeypatch.setattr(run_dotfiles_workflow.shutil, "which", lambda _: None)

    with pytest.raises(SystemExit) as failure:
        run_dotfiles_workflow.resolve_claude_binary()

    assert "claude is not on PATH" in str(failure.value)


def test_workflow_runs_anchored_at_the_repository_root(monkeypatch):
    recorded_invocation = {}

    def record(command, **keyword_arguments):
        recorded_invocation["command"] = command
        recorded_invocation.update(keyword_arguments)
        return completed_workflow(json.dumps({"result": "clean"}))

    monkeypatch.setattr(run_dotfiles_workflow.subprocess, "run", record)

    run_dotfiles_workflow.run_workflow(
        "/nix/store/claude", "/dotfiles-housekeeping {}", Path("/checkouts/dotfiles")
    )

    assert recorded_invocation["cwd"] == Path("/checkouts/dotfiles")
    assert recorded_invocation["timeout"] == (
        run_dotfiles_workflow.WORKFLOW_TIMEOUT_SECONDS
    )
    assert "--strict-mcp-config" in recorded_invocation["command"]
