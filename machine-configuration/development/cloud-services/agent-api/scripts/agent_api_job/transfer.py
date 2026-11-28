import tarfile
from pathlib import PurePosixPath

from agent_api_job.errors import JobError
from agent_api_job.jobs import load_job


def contained_path(working_directory, relative):
    candidate = PurePosixPath(relative)
    forbidden = ("\x00" in relative, candidate.is_absolute(), ".." in candidate.parts)
    if any(forbidden):
        raise JobError("invalid_path")
    base = working_directory.resolve()
    target = (base / candidate).resolve()
    if not target.is_relative_to(base):
        raise JobError("invalid_path")
    if not target.exists():
        raise JobError("path_unavailable")
    return target


def send_path(root, job_id, relative, stream):
    job, _ = load_job(root, job_id)
    target = contained_path(job.working_directory, relative)
    with tarfile.open(fileobj=stream, mode="w|") as archive:
        archive.add(target, arcname=PurePosixPath(relative).as_posix())
    stream.flush()
