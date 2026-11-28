import subprocess
import time

from forge.native import (
    gitlab_json,
    gitlab_pages,
    pipeline_result,
    project_endpoint,
    remaining_timeout,
)
from ci_watcher.transient_failures import (
    RETRY_PAUSE_SECONDS,
    ConsecutiveTransientFailures,
)


def retain_gitlab_trace(repository, directory, job, deadline):
    with (directory / f"job-{job['id']}.log").open("w") as output:
        if not job.get("started_at") and job["status"] in {
            "created",
            "pending",
            "manual",
            "skipped",
            "canceled",
        }:
            output.write(f"Job {job['status']} before execution; no trace available.\n")
            return
        subprocess.run(
            [
                "glab",
                "api",
                f"{project_endpoint(repository)}/jobs/{job['id']}/trace",
                "--hostname",
                repository.hostname,
            ],
            stdout=output,
            stderr=subprocess.STDOUT,
            timeout=remaining_timeout(deadline, 120),
            check=True,
        )


def _pipeline_and_jobs(repository, run, deadline):
    pipeline = gitlab_json(
        repository,
        f"{project_endpoint(repository)}/pipelines/{run}",
        timeout=min(30, deadline - time.monotonic()),
    )
    jobs = gitlab_pages(
        repository,
        f"{project_endpoint(repository)}/pipelines/{run}/jobs",
        deadline=deadline,
    )
    return pipeline, jobs


def _pipeline_snapshot_or_none(repository, run, deadline, failures, progress):
    try:
        snapshot = _pipeline_and_jobs(repository, run, deadline)
    except subprocess.CalledProcessError as error:
        failures.record(f"reading pipeline {run} failed: {error}")
        progress.write("reading the pipeline failed; retrying\n")
        progress.flush()
        return None
    failures.reset()
    return snapshot


def _pause_until_next_read(deadline):
    time.sleep(min(RETRY_PAUSE_SECONDS, max(0, deadline - time.monotonic())))


def watch_gitlab(repository, run, directory, timeout):
    deadline = time.monotonic() + timeout
    retained_jobs = set()
    failures = ConsecutiveTransientFailures()
    with (directory / "watch.log").open("w") as progress:
        while True:
            if deadline - time.monotonic() <= 0:
                raise subprocess.TimeoutExpired("glab", timeout)
            snapshot = _pipeline_snapshot_or_none(
                repository, run, deadline, failures, progress
            )
            if snapshot is None:
                _pause_until_next_read(deadline)
                continue
            pipeline, jobs = snapshot
            result = pipeline_result(pipeline)
            progress.write(f"{pipeline['status']}\n")
            progress.flush()
            _retain_failed_job_traces(
                repository, directory, jobs, deadline, retained_jobs
            )
            if result["status"] == "completed":
                return _complete_gitlab_watch(
                    repository, directory, jobs, result, deadline, retained_jobs
                )
            time.sleep(min(30, max(0, deadline - time.monotonic())))


def _retain_failed_job_traces(repository, directory, jobs, deadline, retained_jobs):
    for job in jobs:
        if job["status"] == "failed" and job["id"] not in retained_jobs:
            retain_gitlab_trace(repository, directory, job, deadline)
            retained_jobs.add(job["id"])


def _complete_gitlab_watch(
    repository, directory, jobs, result, deadline, retained_jobs
):
    for job in jobs:
        if job["id"] not in retained_jobs:
            retain_gitlab_trace(repository, directory, job, deadline)
    _write_gitlab_run_log(directory, jobs)
    passed = result["conclusion"] == "success"
    return {
        **result,
        "jobs": jobs,
        "outcome": "passed" if passed else "failed",
    }, 0 if passed else 1


def _write_gitlab_run_log(directory, jobs):
    with (directory / "run.log").open("w") as output:
        for job in jobs:
            output.write(f"{job['name']} {job['status']} {job['web_url']}\n")
            output.write((directory / f"job-{job['id']}.log").read_text())
