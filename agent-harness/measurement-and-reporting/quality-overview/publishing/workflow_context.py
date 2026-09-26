import argparse
from datetime import datetime
import json
from pathlib import Path
import re
import subprocess

REPOSITORY = "Castrozan/.dotfiles"
ARTIFACT_NAMES = (
    "bats-junit",
    "python-junit",
    "python-coverage",
    "verdr-artifact-evidence",
)


def timestamp(value):
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.utcoffset() is None:
        raise ValueError("Workflow timestamps require a timezone")
    return parsed


def workflow_identity(run):
    expected = {
        "event": "push",
        "head_branch": "main",
        "path": ".github/workflows/tests.yml",
        "status": "completed",
    }
    if any(run.get(key) != value for key, value in expected.items()):
        raise ValueError("Only completed main-push tests runs may publish evidence")
    for field in ("repository", "head_repository"):
        if run[field]["full_name"] != REPOSITORY:
            raise ValueError("Workflow repository differs from the approved producer")
    if not re.fullmatch(r"[a-f0-9]{40}", run["head_sha"]):
        raise ValueError("Workflow revision must be exact")
    if not isinstance(run["run_attempt"], int) or run["run_attempt"] < 1:
        raise ValueError("Workflow attempt must be positive")
    if timestamp(run["run_started_at"]) > timestamp(run["updated_at"]):
        raise ValueError("Workflow timestamps are reversed")
    if not run.get("conclusion"):
        raise ValueError("Completed workflow has no conclusion")
    return {
        "repository": REPOSITORY,
        "revision": run["head_sha"],
        "runId": str(run["id"]),
        "runAttempt": run["run_attempt"],
        "runUrl": f"https://github.com/{REPOSITORY}/actions/runs/{run['id']}",
        "conclusion": run["conclusion"],
        "startedAt": run["run_started_at"],
        "completedAt": run["updated_at"],
    }


def belongs_to_attempt(artifact, workflow):
    origin = artifact.get("workflow_run", {})
    return (
        str(origin.get("id")) == workflow["runId"]
        and origin.get("head_sha") == workflow["revision"]
        and timestamp(workflow["startedAt"])
        <= timestamp(artifact["created_at"])
        <= timestamp(workflow["completedAt"])
    )


def select_artifacts(artifacts, workflow):
    selected = {}
    for name in ARTIFACT_NAMES:
        candidates = [
            artifact
            for artifact in artifacts
            if artifact["name"] == name and belongs_to_attempt(artifact, workflow)
        ]
        if len(candidates) != 1:
            selected[name] = {
                "id": None,
                "reason": f"Expected one {name} artifact for this attempt; found {len(candidates)}",
            }
        elif candidates[0]["expired"]:
            selected[name] = {"id": None, "reason": f"{name} artifact has expired"}
        else:
            selected[name] = {"id": candidates[0]["id"], "reason": None}
    return selected


def build_context(run, jobs, artifacts):
    workflow = workflow_identity(run)
    return {
        "workflow": workflow,
        "jobs": jobs,
        "artifacts": select_artifacts(artifacts, workflow),
    }


def github_document(path):
    approved_route = (
        r"repos/Castrozan/\.dotfiles/(?:commits/main|actions/runs/[1-9]\d*"
        r"(?:/attempts/[1-9]\d*)?(?:/(?:jobs|artifacts)\?per_page=100)?)"
    )
    if not re.fullmatch(approved_route, path, flags=re.ASCII):
        raise ValueError("GitHub route is outside the approved producer metadata")
    result = subprocess.run(
        ["gh", "api", "--method", "GET", "--", path],
        capture_output=True,
        text=True,
        check=True,
        timeout=60,
    )
    return json.loads(result.stdout)


def complete_page(document, key):
    items = document[key]
    if document["total_count"] != len(items):
        raise ValueError(f"Incomplete GitHub {key} inventory")
    return items


def collect_context(event):
    run = event["workflow_run"]
    workflow_identity(run)
    identifier = str(run["id"])
    if not re.fullmatch(r"[1-9]\d*", identifier, flags=re.ASCII):
        raise ValueError("Invalid GitHub workflow run identifier")
    route = f"repos/{REPOSITORY}/actions/runs/{identifier}"
    attempt = f"{route}/attempts/{run['run_attempt']}"
    confirmed = github_document(attempt)
    actual_identity = workflow_identity(confirmed)
    event_identity = workflow_identity(run)
    identity_fields = ("repository", "revision", "runId", "runAttempt")
    if any(actual_identity[key] != event_identity[key] for key in identity_fields):
        raise ValueError("GitHub run identity changed after the completion event")
    jobs = complete_page(github_document(f"{attempt}/jobs?per_page=100"), "jobs")
    artifacts = complete_page(
        github_document(f"{route}/artifacts?per_page=100"), "artifacts"
    )
    return build_context(confirmed, jobs, artifacts)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("event", type=Path)
    parser.add_argument("output", type=Path)
    arguments = parser.parse_args()
    context = collect_context(json.loads(arguments.event.read_text()))
    arguments.output.write_text(json.dumps(context, indent=2) + "\n")
    identifiers = [
        str(item["id"]) for item in context["artifacts"].values() if item["id"]
    ]
    print(",".join(identifiers))


if __name__ == "__main__":
    main()
