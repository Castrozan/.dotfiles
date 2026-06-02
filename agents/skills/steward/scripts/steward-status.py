#!/usr/bin/env python3
"""Read-only maintenance diagnosis for the dotfiles steward agent.

Emits a single JSON object describing the repository and system health so the
steward can decide what to do this heartbeat. Performs exactly one network
mutation (git fetch); everything else is read-only.
"""

import json
import os
import subprocess
import sys
from pathlib import Path


def dotfiles_directory() -> Path:
    return Path(os.environ.get("STEWARD_DOTFILES_DIR", str(Path.home() / ".dotfiles")))


def steward_workspace_directory() -> Path:
    return Path(
        os.environ.get("STEWARD_WORKSPACE_DIR", str(Path.home() / "clawde" / "steward"))
    )


def self_alias() -> str:
    from_environment = os.environ.get("STEWARD_SELF")
    if from_environment:
        return from_environment
    peers_file = steward_workspace_directory() / "peers.json"
    if peers_file.is_file():
        try:
            return json.loads(peers_file.read_text()).get("self", "unknown")
        except json.JSONDecodeError:
            return "unknown"
    return "unknown"


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


def last_validated_revision() -> str:
    stamp = steward_workspace_directory() / "state" / "last-validated-sha"
    return stamp.read_text().strip() if stamp.is_file() else ""


def unread_inbox_messages() -> list[str]:
    inbox = steward_workspace_directory() / "inbox"
    if not inbox.is_dir():
        return []
    return sorted(entry.name for entry in inbox.glob("*.json") if entry.is_file())


def health_check_summary() -> dict:
    return_code, output = run_capturing(["health-check", "--json"], Path.home(), 60)
    if return_code == 127:
        return {"available": False}
    try:
        parsed = json.loads(output)
    except json.JSONDecodeError:
        return {"available": True, "parse_error": True, "exit_code": return_code}
    probes = parsed if isinstance(parsed, list) else parsed.get("probes", [])
    failing = [
        probe for probe in probes if not probe.get("ok", probe.get("passed", True))
    ]
    return {
        "available": True,
        "exit_code": return_code,
        "total": len(probes),
        "failing": [probe.get("name", "?") for probe in failing],
    }


def build_report() -> dict:
    repository = dotfiles_directory()
    branch = current_branch(repository)
    git_output(repository, "fetch", "--quiet", "origin", timeout_seconds=45)

    head_revision = git_output(repository, "rev-parse", "HEAD")
    upstream_revision = git_output(repository, "rev-parse", f"origin/{branch}")
    behind, ahead = divergence_from_upstream(repository, branch)
    dirty = working_tree_is_dirty(repository)
    validated_revision = last_validated_revision()
    inbox = unread_inbox_messages()
    health = health_check_summary()

    health_broken = health.get("available") and bool(health.get("failing"))
    needs_validation = head_revision != validated_revision or dirty
    needs_sync = behind > 0
    needs_push = ahead > 0
    has_mail = bool(inbox)

    if health_broken:
        verdict = "broken"
    elif needs_sync:
        verdict = "needs_sync"
    elif needs_validation:
        verdict = "needs_validation"
    elif needs_push:
        verdict = "needs_push"
    elif has_mail:
        verdict = "has_mail"
    else:
        verdict = "clean"

    return {
        "self": self_alias(),
        "repository": str(repository),
        "branch": branch,
        "head": head_revision,
        "upstream": upstream_revision,
        "behind": behind,
        "ahead": ahead,
        "dirty": dirty,
        "last_validated": validated_revision,
        "needs_sync": needs_sync,
        "needs_validation": needs_validation,
        "needs_push": needs_push,
        "health": health,
        "inbox_unread": inbox,
        "verdict": verdict,
        "attention_required": verdict not in ("clean",),
    }


def main() -> int:
    json.dump(build_report(), sys.stdout, indent=2)
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
