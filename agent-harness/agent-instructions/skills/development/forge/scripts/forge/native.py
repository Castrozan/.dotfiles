import json
import subprocess
import re
import time
from urllib.parse import quote


def capture_json(command, directory=None, timeout=30):
    response = subprocess.run(
        command,
        cwd=directory,
        capture_output=True,
        text=True,
        timeout=timeout,
        check=True,
    )
    return json.loads(response.stdout)


def project_endpoint(repository):
    return f"projects/{quote(repository.project, safe='')}"


def gitlab_json(repository, endpoint, timeout=30):
    return capture_json(
        ["glab", "api", endpoint, "--hostname", repository.hostname], timeout=timeout
    )


def remaining_timeout(deadline, limit=30):
    if deadline is None:
        return limit
    remaining = deadline - time.monotonic()
    if remaining <= 0:
        raise subprocess.TimeoutExpired("glab", limit)
    return min(limit, remaining)


def gitlab_pages(repository, endpoint, deadline=None):
    separator = "&" if "?" in endpoint else "?"
    entries = []
    for page in range(1, 11):
        response = gitlab_json(
            repository,
            f"{endpoint}{separator}per_page=100&page={page}",
            timeout=remaining_timeout(deadline),
        )
        if not isinstance(response, list):
            raise ValueError("GitLab pagination returned a non-list response")
        entries.extend(response)
        if len(response) < 100:
            return entries
    raise RuntimeError(
        "GitLab response exceeds 1000 entries; refusing an incomplete result"
    )


def pipeline_result(pipeline):
    state = pipeline["status"]
    terminal = {"success", "failed", "canceled", "skipped"}
    pending = {
        "created",
        "waiting_for_resource",
        "preparing",
        "pending",
        "running",
        "manual",
        "scheduled",
    }
    if state not in terminal | pending:
        raise ValueError(f"Unknown GitLab pipeline status: {state}")
    return {
        "databaseId": pipeline["id"],
        "attempt": 1,
        "headSha": pipeline["sha"],
        "status": "completed" if state in terminal else "in_progress",
        "conclusion": state if state in terminal else None,
        "workflowName": "pipeline",
        "url": pipeline["web_url"],
    }


def runs_for_revision(repository, revision):
    if not re.fullmatch(r"[0-9a-fA-F]{40}|[0-9a-fA-F]{64}", revision):
        raise ValueError("CI lookup requires a full commit SHA")
    if repository.provider == "github":
        return capture_json(
            [
                "gh",
                "run",
                "list",
                "--repo",
                repository.url,
                "--commit",
                revision,
                "--limit",
                "100",
                "--json",
                "databaseId,headSha,status,conclusion,workflowName,url",
            ]
        )
    pipelines = gitlab_pages(
        repository, f"{project_endpoint(repository)}/pipelines?sha={revision}"
    )
    return [pipeline_result(pipeline) for pipeline in pipelines]


def open_change_requests(repository, branch_prefix):
    if repository.provider == "github":
        return capture_json(
            [
                "gh",
                "pr",
                "list",
                "--repo",
                repository.url,
                "--state",
                "open",
                "--limit",
                "100",
                "--json",
                "number,headRefName,comments",
            ]
        )
    proposals = gitlab_pages(
        repository, f"{project_endpoint(repository)}/merge_requests?state=opened"
    )
    results = []
    for proposal in proposals:
        if not proposal["source_branch"].startswith(branch_prefix):
            continue
        notes = gitlab_pages(
            repository,
            f"{project_endpoint(repository)}/merge_requests/{proposal['iid']}/notes?sort=asc&order_by=created_at",
        )
        results.append(
            {
                "number": proposal["iid"],
                "headRefName": proposal["source_branch"],
                "comments": [
                    {
                        "id": note["id"],
                        "body": note["body"],
                        "createdAt": note["created_at"],
                    }
                    for note in notes
                    if not note.get("system", False)
                ],
            }
        )
    return results
