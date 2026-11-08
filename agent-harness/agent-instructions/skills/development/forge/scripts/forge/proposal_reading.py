from forge.native import capture_json, gitlab_json, gitlab_pages, project_endpoint

GITHUB_DETAIL_FIELDS = "number,headRefName,headRefOid,state,title,body,url,comments"
GITHUB_LISTING_FIELDS = "number,headRefName,title,body,state"
CLOSED_LISTING_LIMIT = "500"


def merge_request_endpoint(repository, number):
    return f"{project_endpoint(repository)}/merge_requests/{number}"


def gitlab_comments(repository, number):
    notes = gitlab_pages(
        repository,
        f"{merge_request_endpoint(repository, number)}/notes?sort=asc&order_by=created_at",
    )
    return [
        {"id": note["id"], "body": note["body"], "createdAt": note["created_at"]}
        for note in notes
        if not note.get("system", False)
    ]


def gitlab_proposal(proposal, comments):
    return {
        "number": proposal["iid"],
        "headRefName": proposal["source_branch"],
        "headRefOid": proposal.get("sha", ""),
        "state": proposal["state"],
        "title": proposal["title"],
        "body": proposal.get("description") or "",
        "url": proposal.get("web_url", ""),
        "comments": comments,
    }


def change_request(repository, number):
    if repository.provider == "github":
        return capture_json(
            [
                "gh",
                "pr",
                "view",
                str(number),
                "--repo",
                repository.url,
                "--json",
                GITHUB_DETAIL_FIELDS,
            ]
        )
    proposal = gitlab_json(repository, merge_request_endpoint(repository, number))
    return gitlab_proposal(proposal, gitlab_comments(repository, number))


def closed_change_requests(repository, branch_prefix):
    if repository.provider == "github":
        listed = capture_json(
            [
                "gh",
                "pr",
                "list",
                "--repo",
                repository.url,
                "--state",
                "closed",
                "--limit",
                CLOSED_LISTING_LIMIT,
                "--json",
                GITHUB_LISTING_FIELDS,
            ]
        )
    else:
        listed = [
            gitlab_proposal(proposal, [])
            for proposal in gitlab_pages(
                repository, f"{project_endpoint(repository)}/merge_requests?state=all"
            )
            if proposal["state"] != "opened"
        ]
    return [
        proposal
        for proposal in listed
        if proposal["headRefName"].startswith(branch_prefix)
    ]
