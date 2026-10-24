import re
from dataclasses import dataclass

from change_requests import ChangeRequest, view_change_request
from command_runner import ReviewTargetError, run_command, run_git

REQUEST_NUMBER_PATTERN = re.compile(r"^[!#]?(\d+)$")
FALLBACK_BASE_BRANCH = "main"


@dataclass(frozen=True)
class ReviewTarget:
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


def resolve_review_target(raw_target: str) -> ReviewTarget:
    selector = raw_target.strip() or run_git(["branch", "--show-current"])
    if not selector:
        raise ReviewTargetError("HEAD is detached: name an MR/PR number or a branch")

    request_number_match = REQUEST_NUMBER_PATTERN.match(selector)
    if request_number_match:
        change_request = view_change_request(request_number_match.group(1))
        if change_request is None:
            raise ReviewTargetError(f"no MR/PR {selector} found on origin")
        head_commit = fetch_commit(change_request.head_fetch_reference)
    else:
        change_request = view_change_request(selector)
        head_commit = local_branch_commit(selector) or fetch_commit(selector)

    base_branch = (
        change_request.base_branch if change_request else default_base_branch()
    )
    base_tip_commit = fetch_commit(base_branch)
    merge_base_commit = run_git(["merge-base", base_tip_commit, head_commit])
    return ReviewTarget(head_commit, merge_base_commit, change_request)
