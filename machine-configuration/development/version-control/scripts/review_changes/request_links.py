import os
import re
from dataclasses import dataclass
from pathlib import Path

from review_command_runner import ReviewTargetError, run_command

REQUEST_LINK_PATTERN = re.compile(
    r"^https?://[^/]+/(?P<project_path>.+?)(?:/-)?/(?:merge_requests|pull)/(?P<number>\d+)"
)
ORIGIN_PROJECT_PATH_PATTERN = re.compile(
    r"^(?:[a-z+]+://)?(?:[^@/]+@)?[^/:]+[:/](?P<project_path>.+?)(?:\.git)?/?$"
)
LOCAL_CLONE_ROOTS = (Path.home() / "repo", Path.home())


@dataclass(frozen=True)
class RequestLink:
    project_path: str
    number: str


def parse_request_link(raw_target: str) -> RequestLink | None:
    link_match = REQUEST_LINK_PATTERN.match(raw_target.strip())
    if not link_match:
        return None
    return RequestLink(link_match["project_path"], link_match["number"])


def origin_project_path(repository_directory: Path) -> str | None:
    result = run_command(
        ["git", "-C", str(repository_directory), "remote", "get-url", "origin"]
    )
    if result.returncode != 0:
        return None
    origin_match = ORIGIN_PROJECT_PATH_PATTERN.match(result.stdout.strip())
    return origin_match["project_path"].lower() if origin_match else None


def candidate_clone_directories(project_path: str) -> list[Path]:
    project_name = project_path.rsplit("/", 1)[-1]
    named_candidates = [root / project_name for root in LOCAL_CLONE_ROOTS]
    scanned_candidates = sorted(
        child for child in LOCAL_CLONE_ROOTS[0].glob("*") if child.is_dir()
    )
    return [Path.cwd(), *named_candidates, *scanned_candidates]


def find_local_clone(project_path: str) -> Path:
    wanted_project_path = project_path.lower()
    for candidate_directory in candidate_clone_directories(project_path):
        if (candidate_directory / ".git").exists() and origin_project_path(
            candidate_directory
        ) == wanted_project_path:
            return candidate_directory
    searched_roots = " or ".join(str(root) for root in LOCAL_CLONE_ROOTS)
    raise ReviewTargetError(f"no local clone of {project_path} in {searched_roots}")


def enter_repository_of(raw_target: str) -> str:
    request_link = parse_request_link(raw_target)
    if request_link is None:
        return raw_target
    os.chdir(find_local_clone(request_link.project_path))
    return request_link.number
