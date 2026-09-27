import argparse
import json
from pathlib import Path
import re
import subprocess

from artifact_selection import ARTIFACT_PRODUCERS, select_artifacts, timestamp

REPOSITORY = "Castrozan/.dotfiles"


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
    if type(run["run_attempt"]) is not int or run["run_attempt"] < 1:
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


def build_context(run, jobs, artifacts, attempts=None):
    workflow = workflow_identity(run)
    return {
        "workflow": workflow,
        "jobs": jobs,
        "artifacts": select_artifacts(
            artifacts, workflow, jobs, attempts or [workflow]
        ),
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


def producing_attempts(workflow, jobs):
    attempts = [workflow]
    producer_names = {name for name, _ in ARTIFACT_PRODUCERS.values()}
    oldest_job = min(
        (
            timestamp(job["started_at"])
            for job in jobs
            if job.get("name") in producer_names and job.get("started_at")
        ),
        default=timestamp(workflow["startedAt"]),
    )
    for number in range(workflow["runAttempt"] - 1, 0, -1):
        if oldest_job >= timestamp(attempts[-1]["startedAt"]):
            break
        route = f"repos/{REPOSITORY}/actions/runs/{workflow['runId']}/attempts/{number}"
        previous = workflow_identity(github_document(route))
        if (
            any(
                previous[key] != workflow[key]
                for key in ("repository", "revision", "runId")
            )
            or previous["runAttempt"] != number
            or timestamp(previous["completedAt"]) > timestamp(attempts[-1]["startedAt"])
        ):
            raise ValueError("Producing attempt history differs from the current run")
        attempts.append(previous)
    return attempts


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
    return build_context(
        confirmed, jobs, artifacts, producing_attempts(actual_identity, jobs)
    )


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
