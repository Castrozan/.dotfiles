from datetime import datetime
import re


ARTIFACT_PRODUCERS = {
    "bats-junit": ("quick-tests", "Retain native Bats test results"),
    "python-junit": ("qml-and-python-tests", "Retain native Python test results"),
    "python-coverage": ("qml-and-python-tests", "Upload Python coverage"),
    "verdr-artifact-evidence": (
        "quality-evidence / artifacts",
        "Retain package identity and independent evidence",
    ),
}


def timestamp(value):
    if not isinstance(value, str):
        raise ValueError("Workflow timestamps must be strings")
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.utcoffset() is None:
        raise ValueError("Workflow timestamps require a timezone")
    return parsed


def _job_matches_workflow(job, workflow):
    return not (
        job.get("status") != "completed"
        or str(job.get("run_id")) != workflow["runId"]
        or job.get("head_sha") != workflow["revision"]
    )


def _attempt_contains_job_interval(attempt, started, completed):
    return (
        timestamp(attempt["startedAt"])
        <= started
        <= completed
        <= timestamp(attempt["completedAt"])
    )


def _verified_job_attempt(attempts, started, completed):
    origins = [
        attempt
        for attempt in attempts
        if _attempt_contains_job_interval(attempt, started, completed)
    ]
    if len(origins) != 1:
        raise ValueError("Producing job has no unique verified attempt interval")
    return origins[0]


def producing_job(jobs, name, workflow, attempts):
    matches = [job for job in jobs if job["name"] == name]
    if len(matches) != 1:
        raise ValueError(f"Expected one producing job {name}; found {len(matches)}")
    job = matches[0]
    if not _job_matches_workflow(job, workflow):
        raise ValueError("Producing job identity differs from the completed run")
    started = timestamp(job["started_at"])
    completed = timestamp(job["completed_at"])
    origin = _verified_job_attempt(attempts, started, completed)
    return job, {
        "jobId": job["id"],
        "jobName": name,
        "runAttempt": origin["runAttempt"],
        "startedAt": job["started_at"],
        "completedAt": job["completed_at"],
    }


def upload_interval(job, step_name):
    matches = [step for step in job["steps"] if step["name"] == step_name]
    if len(matches) != 1 or matches[0].get("conclusion") != "success":
        raise ValueError("Producing job has no successful unique artifact upload")
    step = matches[0]
    started, completed = timestamp(step["started_at"]), timestamp(step["completed_at"])
    if (
        not timestamp(job["started_at"])
        <= started
        <= completed
        <= timestamp(job["completed_at"])
    ):
        raise ValueError("Artifact upload is outside its producing job")
    return started, completed


def _artifact_matches_upload_interval(artifact, name, workflow, started, completed):
    return (
        artifact["name"] == name
        and str(artifact.get("workflow_run", {}).get("id")) == workflow["runId"]
        and artifact.get("workflow_run", {}).get("head_sha") == workflow["revision"]
        and started <= timestamp(artifact["created_at"]) <= completed
    )


def _validate_artifact_digest(artifact, name):
    if not re.fullmatch(r"sha256:[a-f0-9]{64}", artifact.get("digest", "")):
        raise ValueError(f"{name} artifact has no verified archive digest")


def _artifact_identifier_is_valid(artifact):
    return type(artifact["id"]) is int and artifact["id"] >= 1


def select_artifact(artifacts, name, workflow, job, producer):
    started, completed = upload_interval(job, ARTIFACT_PRODUCERS[name][1])
    candidates = [
        artifact
        for artifact in artifacts
        if _artifact_matches_upload_interval(
            artifact, name, workflow, started, completed
        )
    ]
    if len(candidates) != 1:
        raise ValueError(
            f"Expected one {name} artifact for its producing job; found {len(candidates)}"
        )
    artifact = candidates[0]
    if artifact["expired"]:
        raise ValueError(f"{name} artifact has expired")
    _validate_artifact_digest(artifact, name)
    if not _artifact_identifier_is_valid(artifact):
        raise ValueError("Artifact identifier must be positive")
    return {
        "id": artifact["id"],
        "digest": artifact["digest"],
        "producer": producer,
        "reason": None,
    }


def select_artifacts(artifacts, workflow, jobs, attempts):
    selected = {}
    for name, (job_name, _) in ARTIFACT_PRODUCERS.items():
        try:
            job, producer = producing_job(jobs, job_name, workflow, attempts)
            selected[name] = select_artifact(artifacts, name, workflow, job, producer)
        except (KeyError, TypeError, ValueError) as error:
            selected[name] = {"id": None, "reason": str(error)}
    return selected
