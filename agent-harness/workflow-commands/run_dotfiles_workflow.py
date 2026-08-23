import argparse
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

WORKFLOW_NAME_VARIABLE = "DOTFILES_WORKFLOW_NAME"
WORKFLOW_TIMEOUT_SECONDS = 1800
VERBATIM_RELAY_INSTRUCTION = (
    "Return the workflow's report as your entire final message, verbatim. "
    "Add no summary, preamble, commentary, or closing line."
)


def resolve_workflow_name() -> str:
    workflow_name = os.environ.get(WORKFLOW_NAME_VARIABLE, "")
    if not workflow_name:
        raise SystemExit(
            f"{WORKFLOW_NAME_VARIABLE} is unset: run the packaged dotfiles-* command "
            "rather than this script"
        )
    return workflow_name


def parse_command_line(
    workflow_name: str, command_line_arguments: list[str]
) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog=workflow_name,
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
    parser.add_argument(
        "--ref",
        default="",
        help="scope the review to this commit range, read by dotfiles-change-review",
    )
    return parser.parse_args(command_line_arguments)


def resolve_repository_root(requested_root: str) -> Path:
    if requested_root:
        return Path(requested_root).expanduser().resolve()
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


def build_slash_command(
    workflow_name: str, repository_root: Path, review_scope: str
) -> str:
    workflow_arguments = {"root": str(repository_root)}
    if review_scope:
        workflow_arguments["ref"] = review_scope
    return f"/{workflow_name} {json.dumps(workflow_arguments)}"


def resolve_claude_binary() -> str:
    claude_binary = shutil.which("claude")
    if not claude_binary:
        raise SystemExit("claude is not on PATH: run 'rebuild' first")
    return claude_binary


def run_workflow(
    claude_binary: str, slash_command: str, repository_root: Path
) -> subprocess.CompletedProcess:
    return subprocess.run(
        [
            claude_binary,
            "--print",
            slash_command,
            "--output-format",
            "json",
            "--strict-mcp-config",
            "--append-system-prompt",
            VERBATIM_RELAY_INSTRUCTION,
        ],
        cwd=repository_root,
        capture_output=True,
        text=True,
        timeout=WORKFLOW_TIMEOUT_SECONDS,
    )


def extract_report(completed_workflow: subprocess.CompletedProcess) -> str:
    try:
        result_envelope = json.loads(completed_workflow.stdout)
    except json.JSONDecodeError:
        raise SystemExit(
            completed_workflow.stdout.strip()
            or completed_workflow.stderr.strip()
            or "the workflow returned no output"
        )
    report = result_envelope.get("result", "")
    if result_envelope.get("is_error") or not report:
        raise SystemExit(
            report
            or f"the workflow failed: {result_envelope.get('subtype', 'unknown error')}"
        )
    return report


def main() -> int:
    workflow_name = resolve_workflow_name()
    arguments = parse_command_line(workflow_name, sys.argv[1:])
    repository_root = resolve_repository_root(arguments.root)
    slash_command = build_slash_command(workflow_name, repository_root, arguments.ref)
    claude_binary = resolve_claude_binary()
    try:
        completed_workflow = run_workflow(claude_binary, slash_command, repository_root)
    except subprocess.TimeoutExpired:
        raise SystemExit(
            f"the workflow exceeded its {WORKFLOW_TIMEOUT_SECONDS} second ceiling"
        )
    print(extract_report(completed_workflow))
    return 0


if __name__ == "__main__":
    sys.exit(main())
