#!/usr/bin/env python3
"""Read-only maintenance diagnosis for the dotfiles steward agent.

Emits a single JSON object describing the repository and system health so the
steward can decide what to do this heartbeat. The only network reads are git
fetches on the superproject and on each initialized submodule; everything else
is read-only.
"""

import json
import os
import sys
from pathlib import Path

from continuous_integration_status import continuous_integration_status_for_revision
from health_summary import health_check_summary
from repository_status import (
    classify_verdict,
    current_branch,
    divergence_from_upstream,
    git_output,
    run_capturing,
    working_tree_is_dirty,
)
from submodule_status import submodule_report


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


def last_validated_revision() -> str:
    stamp = steward_workspace_directory() / "state" / "last-validated-sha"
    return stamp.read_text().strip() if stamp.is_file() else ""


def unread_inbox_messages() -> list[str]:
    inbox = steward_workspace_directory() / "inbox"
    if not inbox.is_dir():
        return []
    return sorted(entry.name for entry in inbox.glob("*.json") if entry.is_file())


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
    health = health_check_summary(run_capturing)
    continuous_integration = continuous_integration_status_for_revision(
        repository, upstream_revision, run_capturing
    )
    submodules = submodule_report(run_capturing, repository)

    needs_validation = head_revision != validated_revision or dirty
    superproject_divergence = behind > 0 and ahead > 0
    needs_sync = behind > 0 and ahead == 0
    needs_push = ahead > 0 and behind == 0
    has_mail = bool(inbox)
    continuous_integration_failing = continuous_integration.get("state") == "failing"
    continuous_integration_pending = continuous_integration.get("state") == "pending"
    submodule_divergence = submodules["submodule_divergence"]
    needs_submodule_sync = submodules["needs_submodule_sync"]
    needs_submodule_push = submodules["needs_submodule_push"]

    verdict = classify_verdict(
        superproject_divergence=superproject_divergence,
        needs_sync=needs_sync,
        submodule_divergence=submodule_divergence,
        needs_submodule_sync=needs_submodule_sync,
        needs_validation=needs_validation,
        needs_submodule_push=needs_submodule_push,
        needs_push=needs_push,
        continuous_integration_failing=continuous_integration_failing,
        has_mail=has_mail,
        continuous_integration_pending=continuous_integration_pending,
    )

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
        "superproject_divergence": superproject_divergence,
        "needs_sync": needs_sync,
        "needs_validation": needs_validation,
        "needs_push": needs_push,
        "continuous_integration": continuous_integration,
        "continuous_integration_failing": continuous_integration_failing,
        "continuous_integration_pending": continuous_integration_pending,
        "submodules": submodules["submodules"],
        "needs_submodule_sync": needs_submodule_sync,
        "needs_submodule_push": needs_submodule_push,
        "submodule_divergence": submodule_divergence,
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
