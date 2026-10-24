import re
from dataclasses import dataclass

from change_requests import ChangeRequest, view_change_request
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


def find_change_request_for_branch(branch: str) -> ChangeRequest | None:
    try:
        return view_change_request(branch)
    except ReviewTargetError:
        return None


def resolve_head(selector: str) -> tuple[ChangeRequest | None, str]:
    request_number_match = REQUEST_NUMBER_PATTERN.match(selector)
    if not request_number_match:
        change_request = find_change_request_for_branch(selector)
        return change_request, local_branch_commit(selector) or fetch_commit(selector)

    change_request = view_change_request(request_number_match.group(1))
    return change_request, fetch_commit(change_request.head_fetch_reference)


def resolve_review_target(raw_target: str) -> ReviewTarget:
    selector = resolve_selector(raw_target)
    change_request, head_commit = resolve_head(selector)
    base_branch = (
        change_request.base_branch if change_request else default_base_branch()
    )
    base_tip_commit = fetch_commit(base_branch)
    merge_base_commit = run_git(["merge-base", base_tip_commit, head_commit])
    return ReviewTarget(selector, head_commit, merge_base_commit, change_request)
