from pathlib import Path

import pytest

import run_dotfiles_workflow


HOUSEKEEPING_COMMAND = run_dotfiles_workflow.WorkflowCommand(
    command_name="dotfiles-housekeeping",
    workflow_reference={"name": "dotfiles-housekeeping"},
    argument_names=("root", "subtree"),
)


def package_command(monkeypatch, workflow_name="", script_path="", arguments=""):
    monkeypatch.setenv(run_dotfiles_workflow.COMMAND_NAME_VARIABLE, "dotfiles-x")
    monkeypatch.setenv(run_dotfiles_workflow.WORKFLOW_NAME_VARIABLE, workflow_name)
    monkeypatch.setenv(run_dotfiles_workflow.WORKFLOW_SCRIPT_PATH_VARIABLE, script_path)
    monkeypatch.setenv(run_dotfiles_workflow.ARGUMENT_NAMES_VARIABLE, arguments)


def test_a_saved_workflow_is_referenced_by_name(monkeypatch):
    package_command(monkeypatch, workflow_name="compose-page", arguments="brief output")

    command = run_dotfiles_workflow.resolve_workflow_command()

    assert command.workflow_reference == {"name": "compose-page"}
    assert command.argument_names == ("brief", "output")


def test_a_skill_workflow_is_referenced_by_script_path(monkeypatch):
    package_command(monkeypatch, script_path="/nix/store/pulse.workflow.js")

    command = run_dotfiles_workflow.resolve_workflow_command()

    assert command.workflow_reference == {"scriptPath": "/nix/store/pulse.workflow.js"}


@pytest.mark.parametrize(
    "workflow_name, script_path", [("", ""), ("compose-page", "/nix/store/x.js")]
)
def test_running_the_script_directly_names_the_packaged_command(
    monkeypatch, workflow_name, script_path
):
    package_command(monkeypatch, workflow_name=workflow_name, script_path=script_path)

    with pytest.raises(SystemExit) as failure:
        run_dotfiles_workflow.resolve_workflow_command()

    assert "dotfiles-*" in str(failure.value)


def test_help_is_titled_with_the_packaged_command_and_its_arguments(capsys):
    with pytest.raises(SystemExit):
        run_dotfiles_workflow.parse_command_line(HOUSEKEEPING_COMMAND, ["--help"])

    help_text = capsys.readouterr().out
    assert "usage: dotfiles-housekeeping" in help_text
    assert "--subtree" in help_text


def test_the_prompt_carries_the_resolved_root_and_the_requested_arguments():
    arguments = run_dotfiles_workflow.parse_command_line(
        HOUSEKEEPING_COMMAND, ["--subtree", "agent-harness/hooks"]
    )

    workflow_prompt = run_dotfiles_workflow.build_workflow_prompt(
        HOUSEKEEPING_COMMAND, Path("/checkouts/dotfiles"), arguments
    )

    assert workflow_prompt.endswith(
        '{"name": "dotfiles-housekeeping", "args": {"root": "/checkouts/dotfiles", '
        '"subtree": "agent-harness/hooks"}}'
    )


def test_the_prompt_omits_arguments_left_unset():
    compose_command = run_dotfiles_workflow.WorkflowCommand(
        command_name="dotfiles-compose-page",
        workflow_reference={"name": "compose-page"},
        argument_names=("brief", "output", "constraints"),
    )
    arguments = run_dotfiles_workflow.parse_command_line(
        compose_command, ["--brief", "A landing page"]
    )

    workflow_prompt = run_dotfiles_workflow.build_workflow_prompt(
        compose_command, Path("/work"), arguments
    )

    assert workflow_prompt.endswith(
        '{"name": "compose-page", "args": {"brief": "A landing page"}}'
    )
