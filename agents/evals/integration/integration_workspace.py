import os
import subprocess
from pathlib import Path

import yaml

REPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent
SCENARIOS_DIR = Path(__file__).resolve().parent / "scenarios"
CORE_INSTRUCTIONS_PATH = REPO_ROOT / "agents" / "core_rules" / "core.md"


def load_core_instructions_with_frontmatter() -> str:
    return CORE_INSTRUCTIONS_PATH.read_text()


def load_scenario(scenario_path: Path) -> dict:
    with open(scenario_path) as scenario_file:
        return yaml.safe_load(scenario_file)


def validate_file_path_is_relative(file_path: str) -> bool:
    return not os.path.isabs(file_path) and ".." not in file_path


def place_claude_md_and_agents_md_in_workspace(
    workspace_directory: Path,
) -> None:
    agents_md_content = load_core_instructions_with_frontmatter()
    agents_md_path = workspace_directory / "AGENTS.md"
    agents_md_path.write_text(agents_md_content)

    claude_md_path = workspace_directory / "CLAUDE.md"
    claude_md_path.write_text("@AGENTS.md\n")


def setup_scenario_workspace(scenario: dict, workspace_directory: Path) -> None:
    setup = scenario.get("setup", {})

    place_claude_md_and_agents_md_in_workspace(workspace_directory)

    for file_definition in setup.get("files", []):
        relative_path = file_definition["path"]
        if not validate_file_path_is_relative(relative_path):
            raise ValueError(
                f"Scenario file path must be relative without ..: {relative_path}"
            )
        file_path = workspace_directory / relative_path
        file_path.parent.mkdir(parents=True, exist_ok=True)
        file_path.write_text(file_definition["content"])

    if setup.get("git_init", False):
        git_environment = {
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
            env=git_environment,
        )


def sanitize_scenario_name_for_tempdir(
    scenario_name: str,
) -> str:
    return "".join(
        character if character.isalnum() or character in "-_" else "_"
        for character in scenario_name
    )


def discover_scenario_files(
    scenarios_directory: Path,
) -> list[Path]:
    return sorted(scenarios_directory.glob("*.yaml"))
