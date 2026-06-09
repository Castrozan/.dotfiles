import subprocess
from pathlib import Path


def run_capturing(
    arguments: list[str], working_directory: Path, timeout_seconds: int
) -> tuple[int, str]:
    try:
        completed = subprocess.run(
            arguments,
            cwd=str(working_directory),
            capture_output=True,
            text=True,
            timeout=timeout_seconds,
        )
        return completed.returncode, (completed.stdout + completed.stderr).strip()
    except subprocess.TimeoutExpired:
        return 124, f"timeout after {timeout_seconds}s"
    except FileNotFoundError as missing_executable:
        return 127, f"not found: {missing_executable.filename}"


def git_output(repository: Path, *git_arguments: str, timeout_seconds: int = 20) -> str:
    return_code, output = run_capturing(
        ["git", *git_arguments], repository, timeout_seconds
    )
    return output if return_code == 0 else ""


def current_branch(repository: Path) -> str:
    return git_output(repository, "rev-parse", "--abbrev-ref", "HEAD") or "unknown"


def working_tree_is_dirty(repository: Path) -> bool:
    return bool(git_output(repository, "status", "--porcelain"))


def divergence_from_upstream(repository: Path, branch: str) -> tuple[int, int]:
    counts = git_output(
        repository, "rev-list", "--left-right", "--count", f"origin/{branch}...HEAD"
    )
    if not counts:
        return 0, 0
    behind_text, _, ahead_text = counts.partition("\t")
    try:
        return int(behind_text.strip()), int(ahead_text.strip())
    except ValueError:
        return 0, 0


def classify_verdict(
    *,
    superproject_divergence: bool,
    needs_sync: bool,
    submodule_divergence: bool,
    needs_submodule_sync: bool,
    needs_validation: bool,
    needs_submodule_push: bool,
    needs_push: bool,
    continuous_integration_failing: bool,
    has_mail: bool,
    continuous_integration_pending: bool,
) -> str:
    if superproject_divergence:
        return "superproject_divergence"
    if needs_sync:
        return "needs_sync"
    if submodule_divergence:
        return "submodule_divergence"
    if needs_submodule_sync:
        return "needs_submodule_sync"
    if needs_validation:
        return "needs_validation"
    if needs_submodule_push:
        return "needs_submodule_push"
    if needs_push:
        return "needs_push"
    if continuous_integration_failing:
        return "ci_failing"
    if has_mail:
        return "has_mail"
    if continuous_integration_pending:
        return "ci_pending"
    return "clean"
