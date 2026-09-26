import json
from pathlib import Path

from workflow_context import github_document, REPOSITORY, workflow_identity


def promotion_matches(payload, current_head, current_run, current_attempt):
    workflow = payload["workflow"]
    latest = workflow_identity(current_run)
    confirmed = workflow_identity(current_attempt)
    identity_fields = ("repository", "revision", "runId", "runAttempt", "conclusion")
    return (
        current_head == workflow["revision"]
        and all(latest[key] == workflow[key] for key in identity_fields)
        and confirmed == workflow
    )


def main():
    payload = json.loads(Path(".quality-results/overview/payload.json").read_text())
    context = json.loads(Path(".quality-results/workflow-context.json").read_text())
    if payload["workflow"] != context["workflow"]:
        raise ValueError("Stored receipt differs from the expected producing run")
    workflow = payload["workflow"]
    current_head = github_document(f"repos/{REPOSITORY}/commits/main")["sha"]
    current_run = github_document(
        f"repos/{REPOSITORY}/actions/runs/{workflow['runId']}"
    )
    current_attempt = github_document(
        f"repos/{REPOSITORY}/actions/runs/{workflow['runId']}/attempts/{workflow['runAttempt']}"
    )
    matches = promotion_matches(payload, current_head, current_run, current_attempt)
    print("true" if matches else "false")


if __name__ == "__main__":
    main()
