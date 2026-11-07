import argparse
import json
import os
import shutil
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

COMMAND_NAME_VARIABLE = "DOTFILES_WORKFLOW_COMMAND"
WORKFLOW_NAME_VARIABLE = "DOTFILES_WORKFLOW_NAME"
WORKFLOW_SCRIPT_PATH_VARIABLE = "DOTFILES_WORKFLOW_SCRIPT_PATH"
ARGUMENT_NAMES_VARIABLE = "DOTFILES_WORKFLOW_ARGUMENTS"
INTERACTIVE_SESSION_VARIABLES = frozenset(
    {"AGENT_INTERACTIVE_PREFERENCES_PATH", "CLAUDECODE"}
)
WORKFLOW_TIMEOUT_SECONDS = 1800
VERBATIM_RELAY_INSTRUCTION = (
    "Keep your turn open while the workflow runs: once the Workflow tool returns "
    "its run ID, run the Bash command dotfiles-workflow-wait <run ID> with a "
    "600000 ms timeout, and run it again each time it prints still running. "
    "Return the report it prints under the status line as your entire final "
    "message, verbatim. Add no summary, preamble, commentary, or closing line."
)


@dataclass(frozen=True)
class WorkflowCommand:
    command_name: str
    workflow_reference: dict[str, str]
    argument_names: tuple[str, ...]


def resolve_workflow_command() -> WorkflowCommand:
    command_name = os.environ.get(COMMAND_NAME_VARIABLE, "")
    workflow_name = os.environ.get(WORKFLOW_NAME_VARIABLE, "")
    script_path = os.environ.get(WORKFLOW_SCRIPT_PATH_VARIABLE, "")
    if not command_name or bool(workflow_name) == bool(script_path):
        raise SystemExit(
            f"{COMMAND_NAME_VARIABLE} and exactly one of {WORKFLOW_NAME_VARIABLE} or "
            f"{WORKFLOW_SCRIPT_PATH_VARIABLE} must be set: run the packaged "
            "dotfiles-* command rather than this script"
        )
    return WorkflowCommand(
        command_name=command_name,
        workflow_reference=(
            {"name": workflow_name} if workflow_name else {"scriptPath": script_path}
        ),
        argument_names=tuple(os.environ.get(ARGUMENT_NAMES_VARIABLE, "").split()),
    )


def parse_command_line(
    command: WorkflowCommand, command_line_arguments: list[str]
) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog=command.command_name,
        description=(
            "Run a dotfiles workflow from any agent harness and print its report."
        ),
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


def resolve_repository_root(requested_root: str) -> Path:
    if requested_root:
        requested_directory = Path(requested_root).expanduser().resolve()
        if not requested_directory.is_dir():
            raise SystemExit(f"--root {requested_root} is not a directory")
        return requested_directory
    checkout_toplevel = subprocess.run(
        ["git", "rev-parse", "--show-toplevel"],
        capture_output=True,
        text=True,
        check=False,
    )
    if checkout_toplevel.returncode != 0:
        raise SystemExit(
            "the current directory belongs to no git checkout: "
            "pass --root <absolute checkout path>"
        )
    return Path(checkout_toplevel.stdout.strip())


def build_workflow_prompt(
    command: WorkflowCommand, repository_root: Path, arguments: argparse.Namespace
) -> str:
    workflow_arguments = {
        argument_name: (
            str(repository_root)
            if argument_name == "root"
            else getattr(arguments, argument_name)
        )
        for argument_name in command.argument_names
    }
    workflow_input = {
        **command.workflow_reference,
        "args": {name: value for name, value in workflow_arguments.items() if value},
    }
    return f"Call the Workflow tool exactly once with this input: {json.dumps(workflow_input)}"


def resolve_claude_binary() -> str:
    claude_binary = shutil.which("claude")
    if not claude_binary:
        raise SystemExit("claude is not on PATH: run 'rebuild' first")
    return claude_binary


def build_non_interactive_environment() -> dict[str, str]:
    return {
        name: value
        for name, value in os.environ.items()
        if name not in INTERACTIVE_SESSION_VARIABLES
    }


def run_workflow(
    claude_binary: str, workflow_prompt: str, repository_root: Path
) -> subprocess.CompletedProcess:
    return subprocess.run(
        [
            claude_binary,
            "--print",
            workflow_prompt,
            "--output-format",
            "json",
            "--strict-mcp-config",
            "--append-system-prompt",
            VERBATIM_RELAY_INSTRUCTION,
        ],
        cwd=repository_root,
        env=build_non_interactive_environment(),
        capture_output=True,
        text=True,
        timeout=WORKFLOW_TIMEOUT_SECONDS,
    )


def _invalid_workflow_output_message(completed_workflow):
    return (
        completed_workflow.stdout.strip()
        or completed_workflow.stderr.strip()
        or "the workflow returned no output"
    )


def _workflow_failure_message(result_envelope, report):
    return (
        report
        or f"the workflow failed: {result_envelope.get('subtype', 'unknown error')}"
    )


def extract_report(completed_workflow: subprocess.CompletedProcess) -> str:
    try:
        result_envelope = json.loads(completed_workflow.stdout)
    except json.JSONDecodeError:
        raise SystemExit(_invalid_workflow_output_message(completed_workflow))
    report = result_envelope.get("result", "")
    if result_envelope.get("is_error") or not report:
        raise SystemExit(_workflow_failure_message(result_envelope, report))
    return report


def main() -> int:
    command = resolve_workflow_command()
    arguments = parse_command_line(command, sys.argv[1:])
    repository_root = (
        resolve_repository_root(arguments.root)
        if arguments.root or "root" in command.argument_names
        else Path.cwd()
    )
    workflow_prompt = build_workflow_prompt(command, repository_root, arguments)
    claude_binary = resolve_claude_binary()
    try:
        completed_workflow = run_workflow(
            claude_binary, workflow_prompt, repository_root
        )
    except subprocess.TimeoutExpired:
        raise SystemExit(
            f"the workflow exceeded its {WORKFLOW_TIMEOUT_SECONDS} second ceiling"
        )
    print(extract_report(completed_workflow))
    return 0


if __name__ == "__main__":
    sys.exit(main())
