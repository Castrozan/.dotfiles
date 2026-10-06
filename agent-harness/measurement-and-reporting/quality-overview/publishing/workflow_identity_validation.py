import re

from artifact_selection import timestamp


def _validate_expected_run(run):
    expected = {
        "event": "push",
        "head_branch": "main",
        "path": ".github/workflows/tests.yml",
        "status": "completed",
    }
    if any(run.get(key) != value for key, value in expected.items()):
        raise ValueError("Only completed main-push tests runs may publish evidence")


def _validate_run_repositories(run, repository):
    for field in ("repository", "head_repository"):
        if run[field]["full_name"] != repository:
            raise ValueError("Workflow repository differs from the approved producer")


def _validate_run_revision(run):
    if not re.fullmatch(r"[a-f0-9]{40}", run["head_sha"]):
        raise ValueError("Workflow revision must be exact")


def _validate_run_attempt(run):
    if type(run["run_attempt"]) is not int or run["run_attempt"] < 1:
        raise ValueError("Workflow attempt must be positive")


def _validate_run_timestamps(run):
    if timestamp(run["run_started_at"]) > timestamp(run["updated_at"]):
        raise ValueError("Workflow timestamps are reversed")


def _validate_run_conclusion(run):
    if not run.get("conclusion"):
        raise ValueError("Completed workflow has no conclusion")


def validate_workflow_run(run, repository):
    _validate_expected_run(run)
    _validate_run_repositories(run, repository)
    _validate_run_revision(run)
    _validate_run_attempt(run)
    _validate_run_timestamps(run)
    _validate_run_conclusion(run)
