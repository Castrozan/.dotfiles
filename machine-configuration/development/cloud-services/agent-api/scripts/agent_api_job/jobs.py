import shutil
from pathlib import Path

from agent_api_job.errors import JobError
from agent_api_job.model import Job, validate_job_id
from agent_api_job.runners import RUNNERS
from agent_api_job.storage import private_directory, read_json, write_json


def load_job(root, job_id):
    validate_job_id(job_id)
    directory = root / "jobs" / job_id
    spec = read_json(directory / "spec.json")
    if spec is None:
        raise JobError("job_not_found")
    return Job(job_id, directory, Path(spec["working_directory"])), RUNNERS[
        spec["runner"]
    ]


def create_job_directory(root, job_id):
    jobs = private_directory(private_directory(root) / "jobs")
    try:
        (jobs / job_id).mkdir(mode=0o700)
    except FileExistsError:
        raise JobError("job_exists") from None
    return jobs / job_id


def start_job(root, request, runner):
    directory = create_job_directory(root, validate_job_id(request.job))
    job = Job(request.job, directory, request.working_directory)
    write_json(
        directory / "spec.json",
        {"runner": runner.name, "working_directory": str(request.working_directory)},
    )
    try:
        runner.start(job, request.limits, request.command)
    except JobError:
        shutil.rmtree(directory, ignore_errors=True)
        raise
    return {
        "job": request.job,
        "runner": runner.name,
        "limits_enforced": runner.limits_enforced,
    }


def job_status(root, job_id):
    job, runner = load_job(root, job_id)
    return {"job": job_id, **runner.status(job)}


def job_logs(root, job_id, lines):
    job, runner = load_job(root, job_id)
    return {"job": job_id, "log": runner.logs(job, lines)}


def cancel_job(root, job_id):
    job, runner = load_job(root, job_id)
    runner.cancel(job)
    return {"job": job_id, "cancelled": True}
