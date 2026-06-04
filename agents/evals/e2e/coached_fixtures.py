import os
import subprocess
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent
SCENARIOS_DIR = Path(__file__).resolve().parent / "scenarios"
CORE_INSTRUCTIONS_PATH = REPO_ROOT / "agents" / "core_rules" / "core.md"
COMPLIANCE_SKILL_PATH = REPO_ROOT / "agents" / "skills" / "review" / "compliance.md"
E2E_WORKSPACE_PARENT = Path.home() / "repo" / ".e2e-tests"


def load_compliance_skill_body() -> str:
    content = COMPLIANCE_SKILL_PATH.read_text()
    parts = content.split("---", 2)
    if len(parts) >= 3:
        return parts[2].strip()
    return content.strip()


def load_core_instructions_body() -> str:
    content = CORE_INSTRUCTIONS_PATH.read_text()
    parts = content.split("---", 2)
    if len(parts) >= 3:
        return parts[2].strip()
    return content.strip()


def setup_workspace(scenario: dict, workspace: Path) -> None:
    instructions = load_core_instructions_body()
    (workspace / "CLAUDE.md").write_text(instructions + "\n")

    for file_def in scenario.get("setup", {}).get("files", []):
        relative_path = file_def["path"]
        file_path = workspace / relative_path
        file_path.parent.mkdir(parents=True, exist_ok=True)
        file_path.write_text(file_def["content"])

    if scenario.get("setup", {}).get("git_init", False):
        git_env = {
            **os.environ,
            "GIT_AUTHOR_NAME": "test",
            "GIT_AUTHOR_EMAIL": "test@test",
            "GIT_COMMITTER_NAME": "test",
            "GIT_COMMITTER_EMAIL": "test@test",
        }
        subprocess.run(
            ["git", "init"],
            cwd=workspace,
            capture_output=True,
            check=True,
            timeout=10,
        )
        subprocess.run(
            ["git", "add", "."],
            cwd=workspace,
            capture_output=True,
            check=True,
            timeout=10,
        )
        subprocess.run(
            ["git", "commit", "-m", "initial"],
            cwd=workspace,
            capture_output=True,
            check=True,
            timeout=10,
            env=git_env,
        )


def build_coach_prompt(tool_sequence: list[str], workspace: Path) -> str:
    try:
        initial_sha_result = subprocess.run(
            ["git", "rev-list", "--max-parents=0", "HEAD"],
            capture_output=True,
            text=True,
            cwd=workspace,
            timeout=5,
        )
        initial_sha = initial_sha_result.stdout.strip().split("\n")[0]
        diff_result = subprocess.run(
            ["git", "diff", initial_sha],
            capture_output=True,
            text=True,
            cwd=workspace,
            timeout=5,
        )
        git_diff = diff_result.stdout[:3000]
    except Exception:
        git_diff = "(could not get diff)"

    tool_list = " -> ".join(tool_sequence) if tool_sequence else "(no tools used)"

    return (
        f"Review this agent's work for compliance violations.\n\n"
        f"Tool sequence: {tool_list}\n\n"
        f"Git diff:\n```\n{git_diff}\n```\n\n"
        f"Check each rule and report PASS/FAIL/UNKNOWN."
    )
