from pathlib import Path
import sys

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "publishing"))
import workflow_context as CONTEXT


@pytest.fixture
def run():
    return {
        "id": 123,
        "run_attempt": 2,
        "event": "push",
        "head_branch": "main",
        "path": ".github/workflows/tests.yml",
        "status": "completed",
        "conclusion": "failure",
        "head_sha": "a" * 40,
        "repository": {"full_name": CONTEXT.REPOSITORY},
        "head_repository": {"full_name": CONTEXT.REPOSITORY},
        "run_started_at": "2026-09-26T00:10:00Z",
        "updated_at": "2026-09-26T00:20:00Z",
    }


@pytest.fixture
def artifact(run):
    return {
        "id": 456,
        "name": "bats-junit",
        "expired": False,
        "digest": "sha256:" + "a" * 64,
        "created_at": "2026-09-26T00:12:00Z",
        "workflow_run": {"id": run["id"], "head_sha": run["head_sha"]},
    }


@pytest.fixture
def jobs(run):
    return [
        {
            "id": 987,
            "name": "quick-tests",
            "run_id": run["id"],
            "head_sha": run["head_sha"],
            "status": "completed",
            "started_at": run["run_started_at"],
            "completed_at": run["updated_at"],
            "steps": [
                {
                    "name": "Retain native Bats test results",
                    "conclusion": "success",
                    "started_at": "2026-09-26T00:11:59Z",
                    "completed_at": "2026-09-26T00:12:01Z",
                }
            ],
        }
    ]
