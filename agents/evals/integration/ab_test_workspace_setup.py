import os
import subprocess
from pathlib import Path

from ab_test_scenarios import (
    load_core_instructions_body,
    load_core_instructions_with_frontmatter,
)


def initialize_git_repository(
    workspace_directory: Path,
) -> None:
    git_env = {
        **os.environ,
        "GIT_AUTHOR_NAME": "test",
        "GIT_AUTHOR_EMAIL": "test@test",
        "GIT_COMMITTER_NAME": "test",
        "GIT_COMMITTER_EMAIL": "test@test",
    }
    subprocess.run(
        ["git", "init"],
        cwd=workspace_directory,
        capture_output=True,
        timeout=10,
        check=True,
    )
    subprocess.run(
        ["git", "add", "."],
        cwd=workspace_directory,
        capture_output=True,
        timeout=10,
        check=True,
    )
    subprocess.run(
        ["git", "commit", "-m", "initial"],
        cwd=workspace_directory,
        capture_output=True,
        timeout=10,
        check=True,
        env=git_env,
    )


def setup_workspace_with_reference_claude_md(
    workspace_directory: Path,
    files: dict[str, str],
) -> None:
    agents_md_path = workspace_directory / "AGENTS.md"
    agents_md_path.write_text(load_core_instructions_with_frontmatter())

    claude_md_path = workspace_directory / "CLAUDE.md"
    claude_md_path.write_text("@AGENTS.md\n")

    for relative_path, content in files.items():
        file_path = workspace_directory / relative_path
        file_path.parent.mkdir(parents=True, exist_ok=True)
        file_path.write_text(content)

    initialize_git_repository(workspace_directory)


def setup_workspace_with_inline_claude_md(
    workspace_directory: Path,
    files: dict[str, str],
) -> None:
    full_instructions = load_core_instructions_body()

    claude_md_path = workspace_directory / "CLAUDE.md"
    claude_md_path.write_text(full_instructions + "\n")

    for relative_path, content in files.items():
        file_path = workspace_directory / relative_path
        file_path.parent.mkdir(parents=True, exist_ok=True)
        file_path.write_text(content)

    initialize_git_repository(workspace_directory)


def setup_workspace_with_system_prompt(
    workspace_directory: Path,
    files: dict[str, str],
) -> None:
    for relative_path, content in files.items():
        file_path = workspace_directory / relative_path
        file_path.parent.mkdir(parents=True, exist_ok=True)
        file_path.write_text(content)

    initialize_git_repository(workspace_directory)


def setup_workspace_with_no_instructions(
    workspace_directory: Path,
    files: dict[str, str],
) -> None:
    for relative_path, content in files.items():
        file_path = workspace_directory / relative_path
        file_path.parent.mkdir(parents=True, exist_ok=True)
        file_path.write_text(content)

    initialize_git_repository(workspace_directory)


CONFIGURATION_SETUP_FUNCTIONS = {
    "reference": setup_workspace_with_reference_claude_md,
    "inline": setup_workspace_with_inline_claude_md,
    "system-prompt": setup_workspace_with_system_prompt,
    "no-instructions": setup_workspace_with_no_instructions,
}
