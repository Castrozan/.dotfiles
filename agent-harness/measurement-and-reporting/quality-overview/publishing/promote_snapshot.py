import json
from pathlib import Path
import sys

from workflow_context import github_document, REPOSITORY, workflow_identity


def promotion_matches(payload, current_head, current_run):
    workflow = payload["workflow"]
    confirmed = workflow_identity(current_run)
    return current_head == workflow["revision"] and confirmed == workflow


def main(arguments):
    payload = json.loads(Path(arguments[0]).read_text())
    context = json.loads(Path(arguments[1]).read_text())
    if payload["workflow"] != context["workflow"]:
        raise ValueError("Stored receipt differs from the expected producing run")
    workflow = payload["workflow"]
    current_head = github_document(f"repos/{REPOSITORY}/commits/main")["sha"]
    current_run = github_document(
        f"repos/{REPOSITORY}/actions/runs/{workflow['runId']}"
    )
    print("true" if promotion_matches(payload, current_head, current_run) else "false")


if __name__ == "__main__":
    main(sys.argv[1:])
