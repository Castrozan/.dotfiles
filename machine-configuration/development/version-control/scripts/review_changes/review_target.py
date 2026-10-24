import re
from dataclasses import dataclass
from pathlib import Path

from change_requests import ChangeRequest, view_change_request
from request_links import (
    ForgeRepository,
    RequestLink,
    enter_local_clone,
    origin_repository,
    parse_request_link,
)
from review_command_runner import ReviewTargetError, run_command, run_git

REQUEST_NUMBER_PATTERN = re.compile(r"^[!#]?(\d+)$")
FALLBACK_BASE_BRANCH = "main"


@dataclass(frozen=True)
class ReviewTarget:
    selector: str
    head_commit: str
    merge_base_commit: str
    change_request: ChangeRequest | None


def default_base_branch() -> str:
    result = run_command(["git", "symbolic-ref", "--short", "refs/remotes/origin/HEAD"])
    if result.returncode != 0:
        return FALLBACK_BASE_BRANCH
    return result.stdout.strip().removeprefix("origin/")


def fetch_commit(reference: str) -> str:
    run_git(["fetch", "--quiet", "origin", reference])
    return run_git(["rev-parse", "FETCH_HEAD"])


def local_branch_commit(branch: str) -> str | None:
    result = run_command(
        ["git", "rev-parse", "--verify", "--quiet", f"refs/heads/{branch}"]
    )
    if result.returncode != 0:
        return None
    return result.stdout.strip()


def resolve_selector(raw_target: str) -> str:
    selector = raw_target.strip() or run_git(["branch", "--show-current"])
    if not selector:
        raise ReviewTargetError("HEAD is detached: name an MR/PR number or a branch")
    return selector


def current_repository() -> ForgeRepository:
    repository = origin_repository(Path.cwd())
    if repository is None:
        raise ReviewTargetError(
            "not inside a repository with an origin: paste the MR/PR link instead"
        )
    return repository


def parse_request_target(selector: str) -> RequestLink | None:
    request_link = parse_request_link(selector)
    if request_link:
        return request_link
    request_number_match = REQUEST_NUMBER_PATTERN.match(selector)
    if not request_number_match:
        return None
    return RequestLink(current_repository(), request_number_match.group(1))


def find_change_request_for_branch(branch: str) -> ChangeRequest | None:
    repository = origin_repository(Path.cwd())
    if repository is None:
        return None
    try:
        return view_change_request(repository, branch)
    except ReviewTargetError:
        return None


def review_target_against_base(
    selector: str, head_commit: str, change_request: ChangeRequest | None
) -> ReviewTarget:
    base_branch = (
        change_request.base_branch if change_request else default_base_branch()
    )
    base_tip_commit = fetch_commit(base_branch)
    merge_base_commit = run_git(["merge-base", base_tip_commit, head_commit])
    return ReviewTarget(selector, head_commit, merge_base_commit, change_request)


def review_target_of_request(request_link: RequestLink) -> ReviewTarget:
    enter_local_clone(request_link.repository)
    change_request = view_change_request(request_link.repository, request_link.number)
    head_commit = fetch_commit(change_request.head_fetch_reference)
    return review_target_against_base(
        request_link.short_reference, head_commit, change_request
    )


def review_target_of_branch(branch: str) -> ReviewTarget:
    change_request = find_change_request_for_branch(branch)
    head_commit = local_branch_commit(branch) or fetch_commit(branch)
    return review_target_against_base(branch, head_commit, change_request)


def resolve_review_target(
    raw_target: str, default_request: RequestLink | None = None
) -> ReviewTarget:
    if default_request and not raw_target.strip():
        return review_target_of_request(default_request)
    selector = resolve_selector(raw_target)
    request_link = parse_request_target(selector)
    if request_link:
        return review_target_of_request(request_link)
    return review_target_of_branch(selector)
