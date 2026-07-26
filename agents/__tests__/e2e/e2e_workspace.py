import os
import subprocess
import time
from pathlib import Path

import yaml

REPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent
SCENARIOS_DIR = Path(__file__).resolve().parent / "scenarios"
CORE_INSTRUCTIONS_PATH = REPO_ROOT / "agents" / "core_rules" / "core.md"
E2E_WORKSPACE_PARENT = Path.home() / "repo" / ".e2e-tests"


def load_core_instructions_with_frontmatter() -> str:
    return CORE_INSTRUCTIONS_PATH.read_text()


def place_claude_md_in_workspace(
    workspace_directory: Path,
    claude_ab_mode: str = "inline",
) -> None:
    instructions_with_frontmatter = load_core_instructions_with_frontmatter()
    instructions_body_only = instructions_with_frontmatter
    parts = instructions_with_frontmatter.split("---", 2)
    if len(parts) >= 3:
        instructions_body_only = parts[2].strip()

    if claude_ab_mode == "reference":
        (workspace_directory / "AGENTS.md").write_text(instructions_with_frontmatter)
        (workspace_directory / "CLAUDE.md").write_text("@AGENTS.md\n")
    elif claude_ab_mode == "inline":
        (workspace_directory / "CLAUDE.md").write_text(instructions_body_only + "\n")
    elif claude_ab_mode == "global-only":
        pass


def setup_e2e_scenario_workspace(
    scenario: dict,
    workspace_directory: Path,
    claude_ab_mode: str = "inline",
) -> None:
    setup = scenario.get("setup", {})

    project_claude_md_content = setup.get("project_claude_md")
    if project_claude_md_content:
        (workspace_directory / "CLAUDE.md").write_text(project_claude_md_content)
    else:
        place_claude_md_in_workspace(workspace_directory, claude_ab_mode)

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
    with open(scenario_path) as f:
        return yaml.safe_load(f)


def sanitize_name_for_session(name: str) -> str:
    return "".join(c if c.isalnum() or c in "-_" else "-" for c in name)[:40]


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
