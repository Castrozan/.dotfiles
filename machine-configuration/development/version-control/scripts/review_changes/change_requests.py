import json
from dataclasses import dataclass

from request_links import ForgeRepository
from review_command_runner import ReviewTargetError, run_command


@dataclass(frozen=True)
class ChangeRequest:
    title: str
    description: str
    web_url: str
    base_branch: str
    head_branch: str
    head_fetch_reference: str


def forge_lookup_error(result, selector: str) -> ReviewTargetError:
    forge_message = " ".join(result.stderr.split())
    return ReviewTargetError(forge_message or f"no MR/PR {selector} found")


def view_github_pull_request(
    repository: ForgeRepository, selector: str
) -> ChangeRequest:
    result = run_command(
        [
            "gh",
            "pr",
            "view",
            selector,
            "--repo",
            f"{repository.host}/{repository.project_path}",
            "--json",
            "number,title,body,url,baseRefName,headRefName",
        ]
    )
    if result.returncode != 0:
        raise forge_lookup_error(result, selector)
    pull_request = json.loads(result.stdout)
    return ChangeRequest(
        title=pull_request["title"],
        description=pull_request["body"] or "",
        web_url=pull_request["url"],
        base_branch=pull_request["baseRefName"],
        head_branch=pull_request["headRefName"],
        head_fetch_reference=f"pull/{pull_request['number']}/head",
    )


def view_gitlab_merge_request(
    repository: ForgeRepository, selector: str
) -> ChangeRequest:
    result = run_command(
        [
            "glab",
            "mr",
            "view",
            selector,
            "--repo",
            f"https://{repository.host}/{repository.project_path}",
            "--output",
            "json",
        ]
    )
    if result.returncode != 0:
        raise forge_lookup_error(result, selector)
    merge_request = json.loads(result.stdout)
    return ChangeRequest(
        title=merge_request["title"],
        description=merge_request["description"] or "",
        web_url=merge_request["web_url"],
        base_branch=merge_request["target_branch"],
        head_branch=merge_request["source_branch"],
        head_fetch_reference=f"merge-requests/{merge_request['iid']}/head",
    )


def view_change_request(repository: ForgeRepository, selector: str) -> ChangeRequest:
    if repository.is_github:
        return view_github_pull_request(repository, selector)
    return view_gitlab_merge_request(repository, selector)


def format_change_request(change_request: ChangeRequest) -> str:
    return (
        f"# {change_request.title}\n\n"
        f"{change_request.head_branch} -> {change_request.base_branch}\n"
        f"{change_request.web_url}\n\n"
        f"{change_request.description}\n"
    )
