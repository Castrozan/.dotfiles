import argparse
import json
import os
import sys
from dataclasses import dataclass
from pathlib import Path

from archon_runs import report_run, run_archon_json
from workspaces import (
    is_inside_git_checkout,
    resolve_repository_root,
    workspace_arguments,
)

COMMAND_NAME_VARIABLE = "DOTFILES_WORKFLOW_COMMAND"
WORKFLOW_NAME_VARIABLE = "DOTFILES_WORKFLOW_NAME"
ARGUMENT_NAMES_VARIABLE = "DOTFILES_WORKFLOW_ARGUMENTS"
PROVIDER_CONFIGURATIONS_VARIABLE = "DOTFILES_WORKFLOW_PROVIDER_CONFIGURATIONS"
CALLING_HARNESS_MARKERS = (
    ("CLAUDECODE", "claude"),
    ("CODEX_THREAD_ID", "codex"),
    ("OPENCODE", "opencode"),
)


@dataclass(frozen=True)
class WorkflowCommand:
    command_name: str
    workflow_name: str
    argument_names: tuple[str, ...]
    provider_configurations: dict[str, str]


def resolve_workflow_command(environment: dict[str, str]) -> WorkflowCommand:
    command_name = environment.get(COMMAND_NAME_VARIABLE, "")
    workflow_name = environment.get(WORKFLOW_NAME_VARIABLE, "")
    if not command_name or not workflow_name:
        raise SystemExit(
            f"{COMMAND_NAME_VARIABLE} and {WORKFLOW_NAME_VARIABLE} must be set: "
            "run the packaged dotfiles-* command rather than this script"
        )
    return WorkflowCommand(
        command_name=command_name,
        workflow_name=workflow_name,
        argument_names=tuple(environment.get(ARGUMENT_NAMES_VARIABLE, "").split()),
        provider_configurations=json.loads(
            environment.get(PROVIDER_CONFIGURATIONS_VARIABLE, "{}")
        ),
    )


def parse_run_command_line(
    command: WorkflowCommand, command_line_arguments: list[str]
) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog=command.command_name,
        description=(
            "Run a dotfiles workflow through Archon on the calling harness and "
            "print its result."
        ),
    )
    parser.add_argument(
        "--provider",
        choices=sorted(command.provider_configurations),
        help="harness that runs the agent steps, defaulting to the calling harness",
    )
    parser.add_argument(
        "--root",
        default="",
        help=(
            "absolute path of the checkout to work on, "
            "defaulting to the checkout the current directory belongs to"
        ),
    )
    for argument_name in command.argument_names:
        if argument_name != "root":
            parser.add_argument(f"--{argument_name}", default="")
    return parser.parse_args(command_line_arguments)


def detect_calling_provider(environment: dict[str, str]) -> str | None:
    for marker_variable, provider in CALLING_HARNESS_MARKERS:
        if environment.get(marker_variable):
            return provider
    return None


def resolve_provider(
    requested_provider: str | None,
    environment: dict[str, str],
    provider_configurations: dict[str, str],
) -> str:
    provider = requested_provider or detect_calling_provider(environment)
    if provider is None:
        raise SystemExit(
            "cannot tell which harness is calling: pass --provider "
            + "|".join(sorted(provider_configurations))
        )
    if provider not in provider_configurations:
        raise SystemExit(
            f"{provider} cannot run dotfiles workflows yet: pass --provider "
            + "|".join(sorted(provider_configurations))
        )
    return provider


def workflow_inputs(
    command: WorkflowCommand, repository_root: Path, arguments: argparse.Namespace
) -> dict[str, str]:
    supplied_inputs = {
        argument_name: (
            str(repository_root)
            if argument_name == "root"
            else getattr(arguments, argument_name)
        )
        for argument_name in command.argument_names
    }
    return {name: value for name, value in supplied_inputs.items() if value}


def build_launch_command(
    command: WorkflowCommand,
    provider: str,
    workspace: list[str],
    inputs: dict[str, str],
) -> list[str]:
    launch_command = [
        "archon",
        "workflow",
        "run",
        command.workflow_name,
        *workspace,
        "--config",
        command.provider_configurations[provider],
        "--detach",
        "--json",
    ]
    for input_name, input_value in inputs.items():
        launch_command += ["--input", f"{input_name}={input_value}"]
    return launch_command


def run_workflow_command(command_line_arguments: list[str]) -> str:
    command = resolve_workflow_command(dict(os.environ))
    arguments = parse_run_command_line(command, command_line_arguments)
    provider = resolve_provider(
        arguments.provider, dict(os.environ), command.provider_configurations
    )
    working_directory = (
        resolve_repository_root(arguments.root)
        if arguments.root or "root" in command.argument_names
        else Path.cwd()
    )
    launch = run_archon_json(
        build_launch_command(
            command,
            provider,
            workspace_arguments(
                working_directory, is_inside_git_checkout(working_directory)
            ),
            workflow_inputs(command, working_directory, arguments),
        ),
        working_directory,
    )
    return report_run(launch["runId"])


def main() -> int:
    print(run_workflow_command(sys.argv[1:]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
