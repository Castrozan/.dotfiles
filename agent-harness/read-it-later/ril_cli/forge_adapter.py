from __future__ import annotations

import subprocess
from dataclasses import dataclass
from pathlib import Path

from forge.native import open_change_requests
from forge.proposal_reading import change_request, closed_change_requests
from forge.proposal_writing import (
    comment_on_change_request,
    merge_change_request,
    open_change_request,
    replace_change_request_body,
)
from forge.repository import resolve_repository

FORGE_FAILURES = (
    OSError,
    ValueError,
    KeyError,
    RuntimeError,
    subprocess.SubprocessError,
)


class ForgeUnavailable(RuntimeError):
    pass


@dataclass(frozen=True)
class ForgeAdapter:
    repository_directory: Path

    def _call(self, operation, *arguments):
        try:
            repository = resolve_repository(self.repository_directory)
            return operation(repository, *arguments)
        except FORGE_FAILURES as error:
            raise ForgeUnavailable(f"{operation.__name__}: {error}") from error

    def open_pull_requests(self, branch_prefix: str) -> list[dict]:
        listed = self._call(open_change_requests, branch_prefix)
        return [
            pull_request
            for pull_request in listed
            if str(pull_request.get("headRefName", "")).startswith(branch_prefix)
        ]

    def closed_pull_requests(self, branch_prefix: str) -> list[dict]:
        return self._call(closed_change_requests, branch_prefix)

    def pull_request(self, number: int) -> dict:
        return self._call(change_request, number)

    def open_pull_request(self, branch: str, title: str, body: str) -> dict:
        return self._call(open_change_request, branch, "main", title, body)

    def comment(self, number: int, body: str) -> None:
        self._call(comment_on_change_request, number, body)

    def replace_body(self, number: int, body: str) -> None:
        self._call(replace_change_request_body, number, body)

    def merge(self, number: int) -> None:
        self._call(merge_change_request, number)
