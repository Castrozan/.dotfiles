import json
from dataclasses import dataclass

from review_command_runner import run_command, run_git


@dataclass(frozen=True)
class ChangeRequest:
    title: str
    description: str
    web_url: str
    base_branch: str
    head_fetch_reference: str


def origin_is_github() -> bool:
    return "github.com" in run_git(["remote", "get-url", "origin"])


def view_github_pull_request(selector: str) -> ChangeRequest | None:
    result = run_command(
        ["gh", "pr", "view", selector, "--json", "number,title,body,url,baseRefName"]
    )
    if result.returncode != 0:
        return None
    pull_request = json.loads(result.stdout)
    return ChangeRequest(
        title=pull_request["title"],
        description=pull_request["body"] or "",
        web_url=pull_request["url"],
        base_branch=pull_request["baseRefName"],
        head_fetch_reference=f"pull/{pull_request['number']}/head",
    )


def view_gitlab_merge_request(selector: str) -> ChangeRequest | None:
    result = run_command(["glab", "mr", "view", selector, "--output", "json"])
    if result.returncode != 0:
        return None
    merge_request = json.loads(result.stdout)
    return ChangeRequest(
        title=merge_request["title"],
        description=merge_request["description"] or "",
        web_url=merge_request["web_url"],
        base_branch=merge_request["target_branch"],
        head_fetch_reference=f"merge-requests/{merge_request['iid']}/head",
    )


def view_change_request(selector: str) -> ChangeRequest | None:
    if origin_is_github():
        return view_github_pull_request(selector)
    return view_gitlab_merge_request(selector)


def format_change_request(change_request: ChangeRequest) -> str:
    return (
        f"# {change_request.title}\n\n"
        f"{change_request.web_url}\n\n"
        f"{change_request.description}\n"
    )
