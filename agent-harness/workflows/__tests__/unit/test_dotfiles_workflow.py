from pathlib import Path

import pytest

import dotfiles_workflow
from archon_runs import rendered_outcome
from dotfiles_workflow import (
    WorkflowCommand,
    build_launch_command,
    resolve_provider,
    resolve_workflow_command,
    workflow_inputs,
)

PROVIDER_CONFIGURATIONS = {
    "claude": "/store/archon-run-claude.yaml",
    "codex": "/store/archon-run-codex.yaml",
}
HOUSEKEEPING = WorkflowCommand(
    command_name="dotfiles-housekeeping",
    workflow_name="dotfiles-housekeeping",
    argument_names=("root", "subtree"),
    provider_configurations=PROVIDER_CONFIGURATIONS,
)


def test_the_packaged_environment_declares_the_command():
    command = resolve_workflow_command(
        {
            "DOTFILES_WORKFLOW_COMMAND": "dotfiles-housekeeping",
            "DOTFILES_WORKFLOW_NAME": "dotfiles-housekeeping",
            "DOTFILES_WORKFLOW_ARGUMENTS": "root subtree",
            "DOTFILES_WORKFLOW_PROVIDER_CONFIGURATIONS": (
                '{"claude": "/store/archon-run-claude.yaml"}'
            ),
        }
    )
    assert command.argument_names == ("root", "subtree")
    assert command.provider_configurations == {
        "claude": "/store/archon-run-claude.yaml"
    }


def test_running_the_script_directly_is_refused():
    with pytest.raises(SystemExit, match="packaged dotfiles-\\* command"):
        resolve_workflow_command({})


@pytest.mark.parametrize(
    ("environment", "provider"),
    [
        ({"CLAUDECODE": "1"}, "claude"),
        ({"CODEX_THREAD_ID": "01a1"}, "codex"),
    ],
)
def test_the_calling_harness_runs_the_agent_steps(environment, provider):
    assert resolve_provider(None, environment, PROVIDER_CONFIGURATIONS) == provider


def test_an_explicit_provider_wins_over_the_calling_harness():
    assert (
        resolve_provider("codex", {"CLAUDECODE": "1"}, PROVIDER_CONFIGURATIONS)
        == "codex"
    )


def test_an_unknown_caller_must_name_a_provider():
    with pytest.raises(SystemExit, match="pass --provider claude\\|codex"):
        resolve_provider(None, {}, PROVIDER_CONFIGURATIONS)


def test_a_harness_without_a_run_configuration_is_refused():
    with pytest.raises(SystemExit, match="opencode cannot run dotfiles workflows"):
        resolve_provider(None, {"OPENCODE": "1"}, PROVIDER_CONFIGURATIONS)


def test_the_launch_runs_detached_in_place_with_the_provider_configuration():
    launch = build_launch_command(
        HOUSEKEEPING,
        "codex",
        Path("/checkout"),
        {"root": "/checkout", "subtree": "agent-harness"},
    )
    assert launch[:4] == ["archon", "workflow", "run", "dotfiles-housekeeping"]
    assert launch[launch.index("--cwd") + 1] == "/checkout"
    assert launch[launch.index("--config") + 1] == "/store/archon-run-codex.yaml"
    assert {"--detach", "--json"} <= set(launch)
    assert "root=/checkout" in launch and "subtree=agent-harness" in launch


def test_empty_arguments_stay_out_of_the_inputs(monkeypatch):
    monkeypatch.setattr(dotfiles_workflow, "detect_calling_provider", lambda _: None)
    arguments = dotfiles_workflow.parse_run_command_line(
        HOUSEKEEPING, ["--subtree", "agent-harness"]
    )
    assert workflow_inputs(HOUSEKEEPING, Path("/checkout"), arguments) == {
        "root": "/checkout",
        "subtree": "agent-harness",
    }


def test_a_finished_run_prints_its_returned_text():
    record = {
        "status": "completed",
        "terminal_record": {"returns": {"value": "Housekeeping of x: 0 confirmed."}},
    }
    assert rendered_outcome("run", record) == (
        "status=completed\nHousekeeping of x: 0 confirmed."
    )


def test_a_structured_return_prints_as_json():
    record = {
        "status": "completed",
        "terminal_record": {"returns": {"value": {"page": "<main/>"}}},
    }
    assert rendered_outcome("run", record).endswith('"page": "<main/>"\n}')


def test_a_failed_run_prints_its_error():
    record = {
        "status": "failed",
        "terminal_record": {"returns": None, "error": "node slice failed"},
    }
    assert rendered_outcome("run", record) == "status=failed\nnode slice failed"


def test_a_running_workflow_points_at_the_wait_command():
    assert rendered_outcome("abc123", {"status": "running"}) == (
        "status=running: still running; run dotfiles-workflow-wait abc123 again"
    )
