import re
import uuid
from dataclasses import dataclass
from pathlib import Path

from agent_api_job.errors import JobError

CANCEL_MARKER = "cancelled"
LOCK_FILE = "lock"
MAXIMUM_LOG_CHARACTERS = 262144
TREE_KEY_PATTERN = re.compile(r"[a-f0-9]{16,64}")


@dataclass(frozen=True)
class Limits:
    memory_megabytes: int
    cpu_percent: int
    runtime_seconds: int


@dataclass(frozen=True)
class Job:
    identifier: str
    directory: Path
    working_directory: Path


@dataclass(frozen=True)
class StartRequest:
    job: str
    working_directory: Path
    limits: Limits
    command: list


def validate_job_id(value):
    try:
        canonical = str(uuid.UUID(value))
    except ValueError:
        raise JobError("invalid_job") from None
    if canonical != value:
        raise JobError("invalid_job")
    return value


def validate_tree_key(value, code="invalid_key"):
    if not TREE_KEY_PATTERN.fullmatch(value):
        raise JobError(code)
    return value


def job_outcome(state, exit_code=None, result=None):
    return {"state": state, "exit_code": exit_code, "result": result}
