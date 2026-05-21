"""Load the compliance skill body, workspace policy docs, and the recent git diff."""

import subprocess
from pathlib import Path

CORE_RULES_PATH = Path.home() / ".dotfiles" / "agents" / "core.md"

COMPLIANCE_SKILL_PATH = (
    Path.home() / ".dotfiles" / "agents" / "skills" / "review" / "compliance.md"
)

WORKSPACE_POLICY_DOC_FILENAMES = [
    "CLAUDE.md",
    "AGENTS.md",
    "README.md",
    "CONTRIBUTING.md",
]

MAX_WORKSPACE_DOC_CHARS = 3000

MAX_DIFF_CHARS = 2000


def strip_yaml_frontmatter(markdown_body: str) -> str:
    if not markdown_body.startswith("---"):
        return markdown_body
    closing_delimiter_index = markdown_body.find("\n---", 3)
    if closing_delimiter_index == -1:
        return markdown_body
    return markdown_body[closing_delimiter_index + len("\n---") :].lstrip()


def load_core_rules_body() -> str:
    if not CORE_RULES_PATH.exists():
        return ""
    return strip_yaml_frontmatter(CORE_RULES_PATH.read_text()).strip()


def load_compliance_skill_body() -> str:
    compliance_text = ""
    if COMPLIANCE_SKILL_PATH.exists():
        compliance_text = COMPLIANCE_SKILL_PATH.read_text().strip()
    core_rules_text = load_core_rules_body()
    if not core_rules_text:
        return compliance_text
    if not compliance_text:
        return f"<core-rules-reinforcement>\n{core_rules_text}\n</core-rules-reinforcement>"
    return (
        f"<core-rules-reinforcement>\n{core_rules_text}\n</core-rules-reinforcement>\n\n"
        f"{compliance_text}"
    )


def load_workspace_policy_docs(workspace_cwd: str) -> dict[str, str]:
    if not workspace_cwd:
        return {}
    discovered_docs: dict[str, str] = {}
    workspace_root = Path(workspace_cwd)
    for filename in WORKSPACE_POLICY_DOC_FILENAMES:
        candidate_path = workspace_root / filename
        if not candidate_path.is_file():
            continue
        try:
            file_text = candidate_path.read_text()
        except OSError:
            continue
        discovered_docs[filename] = file_text[:MAX_WORKSPACE_DOC_CHARS]
    return discovered_docs


def _run_git_command(arguments: list[str], workspace_cwd: str) -> str:
    git_run_options = {
        "capture_output": True,
        "text": True,
        "timeout": 5,
        "cwd": workspace_cwd if workspace_cwd else None,
    }
    try:
        completed = subprocess.run(["git", *arguments], **git_run_options)
    except Exception:
        return ""
    if completed.returncode != 0:
        return ""
    return completed.stdout


def _find_oldest_commit_sha_since(workspace_cwd: str, since_timestamp: str) -> str:
    if not since_timestamp:
        return ""
    log_output = _run_git_command(
        ["log", f"--since={since_timestamp}", "--pretty=format:%H"], workspace_cwd
    )
    commit_shas = [line for line in log_output.strip().splitlines() if line.strip()]
    if not commit_shas:
        return ""
    return commit_shas[-1]


def get_recent_git_diff(workspace_cwd: str, session_start_timestamp: str = "") -> str:
    diff_sections: list[str] = []

    session_commits_diff = ""
    oldest_session_commit_sha = _find_oldest_commit_sha_since(
        workspace_cwd, session_start_timestamp
    )
    if oldest_session_commit_sha:
        parent_revision = _run_git_command(
            ["rev-parse", f"{oldest_session_commit_sha}^"], workspace_cwd
        ).strip()
        base_revision = parent_revision or oldest_session_commit_sha
        session_commits_diff = _run_git_command(
            ["diff", f"{base_revision}..HEAD"], workspace_cwd
        )
    if session_commits_diff.strip():
        diff_sections.append(f"# session commits\n{session_commits_diff}")

    staged_diff = _run_git_command(["diff", "--cached"], workspace_cwd)
    if staged_diff.strip():
        diff_sections.append(f"# staged (uncommitted)\n{staged_diff}")

    unstaged_diff = _run_git_command(["diff"], workspace_cwd)
    if unstaged_diff.strip():
        diff_sections.append(f"# unstaged (working tree)\n{unstaged_diff}")

    combined = "\n\n".join(diff_sections)
    return combined[:MAX_DIFF_CHARS]
