import os
import subprocess
import time
from pathlib import Path

import yaml

from e2e_harness_profiles import CLAUDE_PROFILE, HarnessProfile

REPO_ROOT = Path(__file__).resolve().parents[4]
SCENARIOS_DIR = Path(__file__).resolve().parent / "scenarios"
CORE_INSTRUCTIONS_PATH = (
    REPO_ROOT / "agent-harness" / "agent-instructions" / "core-rules" / "core.md"
)
E2E_WORKSPACE_PARENT = Path.home() / "repo" / ".e2e-tests"
IMPORTED_INSTRUCTION_FILENAME = "AGENTS.md"


def load_core_instructions() -> str:
    return CORE_INSTRUCTIONS_PATH.read_text()


def place_core_instructions_in_workspace(
    workspace_directory: Path,
    profile: HarnessProfile = CLAUDE_PROFILE,
    instruction_placement_mode: str = "inline",
) -> None:
    if instruction_placement_mode == "global-only":
        return

    core_instructions = load_core_instructions()
    project_instruction_path = (
        workspace_directory / profile.project_instruction_filename
    )

    if instruction_placement_mode == "reference" and (
        profile.supports_instruction_reference_import
    ):
        (workspace_directory / IMPORTED_INSTRUCTION_FILENAME).write_text(
            core_instructions
        )
        project_instruction_path.write_text(f"@{IMPORTED_INSTRUCTION_FILENAME}\n")
        return

    project_instruction_path.write_text(core_instructions.rstrip() + "\n")


def setup_e2e_scenario_workspace(
    scenario: dict,
    workspace_directory: Path,
    profile: HarnessProfile = CLAUDE_PROFILE,
    instruction_placement_mode: str = "inline",
) -> None:
    setup = scenario.get("setup", {})

    project_instructions = setup.get("project_instructions")
    if project_instructions:
        (workspace_directory / profile.project_instruction_filename).write_text(
            project_instructions
        )
    else:
        place_core_instructions_in_workspace(
            workspace_directory, profile, instruction_placement_mode
        )

    for file_def in setup.get("files", []):
        relative_path = file_def["path"]
        if os.path.isabs(relative_path) or ".." in relative_path:
            raise ValueError(f"path must be relative: {relative_path}")
        file_path = workspace_directory / relative_path
        file_path.parent.mkdir(parents=True, exist_ok=True)
        file_path.write_text(file_def["content"])

    if setup.get("git_init", False):
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
            check=True,
            timeout=10,
        )
        subprocess.run(
            ["git", "config", "core.hooksPath", "/dev/null"],
            cwd=workspace_directory,
            capture_output=True,
            check=True,
            timeout=10,
        )
        subprocess.run(
            ["git", "add", "."],
            cwd=workspace_directory,
            capture_output=True,
            check=True,
            timeout=10,
        )
        subprocess.run(
            ["git", "commit", "-m", "initial"],
            cwd=workspace_directory,
            capture_output=True,
            check=True,
            timeout=10,
            env=git_env,
        )


def load_scenario(scenario_path: Path) -> dict:
    with open(scenario_path) as scenario_file:
        return yaml.safe_load(scenario_file)


def sanitize_name_for_session(name: str) -> str:
    return "".join(
        character if character.isalnum() or character in "-_" else "-"
        for character in name
    )[:40]


def discover_scenario_files(
    scenarios_dir: Path,
) -> list[Path]:
    return sorted(scenarios_dir.rglob("*.yaml"))


def save_debug_capture(scenario_name: str, raw_output: str) -> None:
    debug_directory = Path("/tmp/e2e-debug-captures")
    debug_directory.mkdir(exist_ok=True)
    timestamp = int(time.time())
    output_file = debug_directory / f"{scenario_name}-{timestamp}.txt"
    output_file.write_text(raw_output)
    print(f"    Debug capture saved: {output_file}")
