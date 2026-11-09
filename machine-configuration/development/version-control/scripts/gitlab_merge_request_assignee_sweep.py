import argparse
import json
import subprocess
import sys
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Protocol
from urllib.parse import urlencode

RECENT_MERGE_REQUEST_WINDOW = timedelta(hours=24)
GLAB_COMMAND_TIMEOUT_SECONDS = 30
MERGE_REQUESTS_PER_SWEEP = 100
FAILURE_MESSAGE_CHARACTER_LIMIT = 300


class GitLabRequestFailed(Exception):
    pass


@dataclass(frozen=True)
class MergeRequest:
    project_id: int
    internal_id: int
    author_id: int
    assignee_ids: tuple[int, ...]
    web_url: str


@dataclass(frozen=True)
class SweepResult:
    assigned: tuple[MergeRequest, ...]
    failures: tuple[str, ...]


class MergeRequestGateway(Protocol):
    def list_unassigned_authored_since(
        self, created_after: datetime
    ) -> list[MergeRequest]: ...

    def read(self, listed: MergeRequest) -> MergeRequest: ...

    def assign(self, current: MergeRequest, assignee_id: int) -> None: ...


def merge_request_from_api(payload: dict) -> MergeRequest:
    return MergeRequest(
        project_id=payload["project_id"],
        internal_id=payload["iid"],
        author_id=payload["author"]["id"],
        assignee_ids=tuple(assignee["id"] for assignee in payload["assignees"]),
        web_url=payload["web_url"],
    )


class GlabMergeRequestGateway:
    def __init__(self, host: str) -> None:
        self._host = host

    def list_unassigned_authored_since(
        self, created_after: datetime
    ) -> list[MergeRequest]:
        query = urlencode(
            {
                "scope": "created_by_me",
                "state": "opened",
                "assignee_id": "None",
                "created_after": created_after.isoformat(),
                "per_page": MERGE_REQUESTS_PER_SWEEP,
            }
        )
        payload = self._request(f"merge_requests?{query}")
        return [merge_request_from_api(item) for item in payload]

    def read(self, listed: MergeRequest) -> MergeRequest:
        return merge_request_from_api(self._request(_merge_request_path(listed)))

    def assign(self, current: MergeRequest, assignee_id: int) -> None:
        self._request(
            "-X",
            "PUT",
            _merge_request_path(current),
            "-F",
            f"assignee_id={assignee_id}",
        )

    def _request(self, *arguments: str):
        command = ["glab", "api", "--hostname", self._host, *arguments]
        try:
            completed = subprocess.run(
                command,
                capture_output=True,
                text=True,
                timeout=GLAB_COMMAND_TIMEOUT_SECONDS,
                check=False,
            )
        except subprocess.TimeoutExpired as timeout:
            raise GitLabRequestFailed("glab timed out") from timeout
        if completed.returncode != 0:
            raise GitLabRequestFailed(
                completed.stderr.strip()[:FAILURE_MESSAGE_CHARACTER_LIMIT]
            )
        try:
            return json.loads(completed.stdout)
        except json.JSONDecodeError as malformed:
            raise GitLabRequestFailed("glab returned malformed JSON") from malformed


def _merge_request_path(merge_request: MergeRequest) -> str:
    return (
        f"projects/{merge_request.project_id}"
        f"/merge_requests/{merge_request.internal_id}"
    )


def read_or_record_first_sweep_time(marker: Path, now: datetime) -> datetime:
    if marker.exists():
        return datetime.fromisoformat(marker.read_text(encoding="utf-8").strip())
    marker.parent.mkdir(parents=True, exist_ok=True)
    marker.write_text(now.isoformat(), encoding="utf-8")
    return now


def sweep_lower_bound(first_sweep: datetime, now: datetime) -> datetime:
    return max(first_sweep, now - RECENT_MERGE_REQUEST_WINDOW)


def fill_missing_assignees(
    gateway: MergeRequestGateway, created_after: datetime
) -> SweepResult:
    assigned: list[MergeRequest] = []
    failures: list[str] = []
    for listed in gateway.list_unassigned_authored_since(created_after):
        try:
            current = gateway.read(listed)
            if current.assignee_ids:
                continue
            gateway.assign(current, current.author_id)
        except GitLabRequestFailed as failure:
            failures.append(f"{listed.web_url}: {failure}")
            continue
        assigned.append(current)
    return SweepResult(tuple(assigned), tuple(failures))


def sweep_host(
    host: str,
    gateway: MergeRequestGateway,
    state_directory: Path,
    now: datetime,
) -> SweepResult:
    marker = state_directory / f"{host}.first-sweep-at"
    first_sweep = read_or_record_first_sweep_time(marker, now)
    return fill_missing_assignees(gateway, sweep_lower_bound(first_sweep, now))


def parse_arguments(arguments: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Assign recently opened, unassigned merge requests to their author."
    )
    parser.add_argument("--host", action="append", required=True)
    parser.add_argument("--state-directory", type=Path, required=True)
    return parser.parse_args(arguments)


def main(arguments: list[str]) -> int:
    parsed = parse_arguments(arguments)
    now = datetime.now(UTC)
    failed = False
    for host in parsed.host:
        try:
            result = sweep_host(
                host, GlabMergeRequestGateway(host), parsed.state_directory, now
            )
        except GitLabRequestFailed as failure:
            print(f"{host}: {failure}", file=sys.stderr)
            failed = True
            continue
        for merge_request in result.assigned:
            print(f"assigned {merge_request.web_url}")
        for failure in result.failures:
            print(failure, file=sys.stderr)
        failed = failed or bool(result.failures)
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
