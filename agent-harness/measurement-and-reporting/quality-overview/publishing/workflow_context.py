import argparse
import json
from pathlib import Path
import re
import subprocess
from time import monotonic, sleep

from artifact_selection import ARTIFACT_PRODUCERS, select_artifacts, timestamp
import workflow_identity_validation

REPOSITORY = "Castrozan/.dotfiles"


def workflow_identity(run):
    workflow_identity_validation.validate_workflow_run(run, REPOSITORY)
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


def _producer_job_is_incomplete(job, producer_names):
    if job.get("name") not in producer_names:
        return False
    if job.get("status") != "completed":
        return True
    if not job.get("steps") and job.get("conclusion") == "success":
        return True
    return any(
        step.get("status") in {"pending", "in_progress"}
        for step in job.get("steps", [])
    )


def _has_incomplete_producer(jobs, producer_names):
    return any(_producer_job_is_incomplete(job, producer_names) for job in jobs)


def _wait_for_job_steps(deadline):
    remaining = deadline - monotonic()
    if remaining <= 0:
        raise ValueError("Completed producing jobs still have incomplete step metadata")
    sleep(min(20, remaining))


def completed_job_inventory(attempt):
    deadline = monotonic() + 600
    producer_names = {name for name, _ in ARTIFACT_PRODUCERS.values()}
    while True:
        jobs = complete_page(github_document(f"{attempt}/jobs?per_page=100"), "jobs")
        if not _has_incomplete_producer(jobs, producer_names):
            return jobs
        _wait_for_job_steps(deadline)


def _attempt_differs_from_current(previous, workflow, number, prior_attempt):
    return (
        any(
            previous[key] != workflow[key]
            for key in ("repository", "revision", "runId")
        )
        or previous["runAttempt"] != number
        or timestamp(previous["completedAt"]) > timestamp(prior_attempt["startedAt"])
    )


def _oldest_producing_job_start(jobs, producer_names, workflow):
    return min(
        (
            timestamp(job["started_at"])
            for job in jobs
            if job.get("name") in producer_names and job.get("started_at")
        ),
        default=timestamp(workflow["startedAt"]),
    )


def producing_attempts(workflow, jobs):
    attempts = [workflow]
    producer_names = {name for name, _ in ARTIFACT_PRODUCERS.values()}
    oldest_job = _oldest_producing_job_start(jobs, producer_names, workflow)
    for number in range(workflow["runAttempt"] - 1, 0, -1):
        if oldest_job >= timestamp(attempts[-1]["startedAt"]):
            break
        route = f"repos/{REPOSITORY}/actions/runs/{workflow['runId']}/attempts/{number}"
        previous = workflow_identity(github_document(route))
        if _attempt_differs_from_current(previous, workflow, number, attempts[-1]):
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
    jobs = completed_job_inventory(attempt)
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
