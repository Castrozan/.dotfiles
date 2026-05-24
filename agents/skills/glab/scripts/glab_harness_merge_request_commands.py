"""Merge-request operations: view, create, update, changes, discussions, close, merge."""

import sys

from glab_harness_api_client import (
    encoded_project_path,
    gitlab_api_request,
    resolve_comma_separated_usernames_to_ids,
)


def command_merge_request_view(args, token, project, host):
    project_encoded = encoded_project_path(project)
    merge_request = gitlab_api_request(
        "GET",
        f"projects/{project_encoded}/merge_requests/{args.iid}",
        token,
        host=host,
    )

    print(f"!{merge_request['iid']} | {merge_request['title']}")
    print(f"State: {merge_request['state']}")
    print(
        f"Source: {merge_request['source_branch']} -> {merge_request['target_branch']}"
    )
    print(f"Author: {merge_request['author']['username']}")

    assignee_names = ", ".join(
        a["username"] for a in merge_request.get("assignees", [])
    )
    reviewer_names = ", ".join(
        r["username"] for r in merge_request.get("reviewers", [])
    )
    merge_status = merge_request.get(
        "detailed_merge_status", merge_request.get("merge_status")
    )

    print(f"Assignees: {assignee_names}")
    print(f"Reviewers: {reviewer_names}")
    print(f"Has conflicts: {merge_request.get('has_conflicts')}")
    print(f"Merge status: {merge_status}")
    print(f"URL: {merge_request['web_url']}")

    if merge_request.get("description"):
        print(f"\n{merge_request['description']}")


def command_merge_request_create(args, token, project, host):
    project_encoded = encoded_project_path(project)

    body = {
        "source_branch": args.source,
        "target_branch": args.target,
        "title": args.title,
    }

    if args.description_file:
        with open(args.description_file) as description_file:
            body["description"] = description_file.read()

    if args.remove_source_branch:
        body["remove_source_branch"] = True

    if args.assignee:
        body["assignee_ids"] = resolve_comma_separated_usernames_to_ids(
            args.assignee, token, host
        )

    if args.reviewer:
        body["reviewer_ids"] = resolve_comma_separated_usernames_to_ids(
            args.reviewer, token, host
        )

    merge_request = gitlab_api_request(
        "POST",
        f"projects/{project_encoded}/merge_requests",
        token,
        body=body,
        host=host,
    )
    print(f"!{merge_request['iid']} | {merge_request['title']}")
    print(merge_request["web_url"])


def command_merge_request_update(args, token, project, host):
    project_encoded = encoded_project_path(project)

    body = {}
    if args.title:
        body["title"] = args.title
    if args.description_file:
        with open(args.description_file) as description_file:
            body["description"] = description_file.read()
    if args.assignee:
        body["assignee_ids"] = resolve_comma_separated_usernames_to_ids(
            args.assignee, token, host
        )
    if args.reviewer:
        body["reviewer_ids"] = resolve_comma_separated_usernames_to_ids(
            args.reviewer, token, host
        )

    if not body:
        print("Error: no update fields provided", file=sys.stderr)
        sys.exit(1)

    merge_request = gitlab_api_request(
        "PUT",
        f"projects/{project_encoded}/merge_requests/{args.iid}",
        token,
        body=body,
        host=host,
    )
    print(f"!{merge_request['iid']} | {merge_request['title']}")
    print(merge_request["web_url"])


def command_merge_request_changes(args, token, project, host):
    project_encoded = encoded_project_path(project)
    data = gitlab_api_request(
        "GET",
        f"projects/{project_encoded}/merge_requests/{args.iid}/changes",
        token,
        host=host,
    )
    changes = data.get("changes", [])
    print(f"{len(changes)} files changed:")
    for change in changes:
        print(f"  {change['new_path']}")


def command_merge_request_discussions(args, token, project, host):
    project_encoded = encoded_project_path(project)
    discussions = gitlab_api_request(
        "GET",
        f"projects/{project_encoded}/merge_requests/{args.iid}/discussions?per_page=100",
        token,
        host=host,
    )

    found_comments = False
    for discussion in discussions:
        for note in discussion.get("notes", []):
            if note.get("system"):
                continue

            found_comments = True
            author = note["author"]["name"]
            username = note["author"]["username"]
            position = note.get("position")

            if position:
                file_path = position.get("new_path", "?")
                line_number = position.get("new_line", "?")
                print(f"--- {author} ({username}) on {file_path}:{line_number} ---")
            else:
                print(f"--- {author} ({username}) ---")

            print(note["body"])
            print()

    if not found_comments:
        print("No comments on this merge request.")


def command_merge_request_close(args, token, project, host):
    project_encoded = encoded_project_path(project)
    merge_request = gitlab_api_request(
        "PUT",
        f"projects/{project_encoded}/merge_requests/{args.iid}",
        token,
        body={"state_event": "close"},
        host=host,
    )
    print(f"!{merge_request['iid']} closed")


def command_merge_request_merge(args, token, project, host):
    project_encoded = encoded_project_path(project)
    body = {}
    if args.squash:
        body["squash"] = True
    merge_request = gitlab_api_request(
        "PUT",
        f"projects/{project_encoded}/merge_requests/{args.iid}/merge",
        token,
        body=body,
        host=host,
    )
    print(f"!{merge_request['iid']} merged")
