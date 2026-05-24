#!/usr/bin/env python3
import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from glab_harness_api_client import (  # noqa: E402, F401
    encoded_project_path,
    gitlab_api_request,
    resolve_comma_separated_usernames_to_ids,
    resolve_username_to_id,
)
from glab_harness_gitlab_host_and_token import (  # noqa: E402, F401
    GITLAB_HOST_COATES,
    GITLAB_HOST_PUBLIC,
    GITLAB_TOKEN_ENVIRONMENT_VARIABLE_NAME_BY_HOST,
    GITLAB_TOKEN_SECRET_FILE_PATH_BY_HOST,
    resolve_git_remote_url,
    resolve_gitlab_host_from_remote_url,
    resolve_gitlab_token,
    resolve_project_path_from_remote_url,
)
from glab_harness_merge_request_commands import (  # noqa: E402, F401
    command_merge_request_changes,
    command_merge_request_close,
    command_merge_request_create,
    command_merge_request_discussions,
    command_merge_request_merge,
    command_merge_request_update,
    command_merge_request_view,
)
from glab_harness_pipeline_and_branch_commands import (  # noqa: E402, F401
    command_delete_branch,
    command_pipeline_jobs,
    command_pipelines,
)
from glab_harness_user_events_command import (  # noqa: E402, F401
    USER_EVENTS_HOST_ALIAS_TO_HOSTS,
    command_user_events,
)

COMMANDS_THAT_DO_NOT_REQUIRE_GIT_REPO_CONTEXT = {"user-events"}


def build_argument_parser():
    parser = argparse.ArgumentParser(description="GitLab harness for agent operations")
    subparsers = parser.add_subparsers(dest="command", required=True)

    merge_request_view_parser = subparsers.add_parser("mr-view")
    merge_request_view_parser.add_argument("iid", type=int)

    merge_request_create_parser = subparsers.add_parser("mr-create")
    merge_request_create_parser.add_argument("--source", required=True)
    merge_request_create_parser.add_argument("--target", required=True)
    merge_request_create_parser.add_argument("--title", required=True)
    merge_request_create_parser.add_argument("--description-file")
    merge_request_create_parser.add_argument("--assignee")
    merge_request_create_parser.add_argument("--reviewer")
    merge_request_create_parser.add_argument(
        "--remove-source-branch", action="store_true"
    )

    merge_request_update_parser = subparsers.add_parser("mr-update")
    merge_request_update_parser.add_argument("iid", type=int)
    merge_request_update_parser.add_argument("--title")
    merge_request_update_parser.add_argument("--description-file")
    merge_request_update_parser.add_argument("--assignee")
    merge_request_update_parser.add_argument("--reviewer")

    merge_request_changes_parser = subparsers.add_parser("mr-changes")
    merge_request_changes_parser.add_argument("iid", type=int)

    merge_request_discussions_parser = subparsers.add_parser("mr-discussions")
    merge_request_discussions_parser.add_argument("iid", type=int)

    merge_request_close_parser = subparsers.add_parser("mr-close")
    merge_request_close_parser.add_argument("iid", type=int)

    merge_request_merge_parser = subparsers.add_parser("mr-merge")
    merge_request_merge_parser.add_argument("iid", type=int)
    merge_request_merge_parser.add_argument("--squash", action="store_true")

    pipelines_parser = subparsers.add_parser("pipelines")
    pipelines_parser.add_argument("--ref")
    pipelines_parser.add_argument("--count", type=int, default=5)

    pipeline_jobs_parser = subparsers.add_parser("pipeline-jobs")
    pipeline_jobs_parser.add_argument("pipeline_id", type=int)

    delete_branch_parser = subparsers.add_parser("delete-branch")
    delete_branch_parser.add_argument("branch_name")

    user_events_parser = subparsers.add_parser(
        "user-events",
        help="List the authenticated user's events for a date across one or both GitLab hosts.",
    )
    user_events_parser.add_argument(
        "--host",
        choices=sorted(USER_EVENTS_HOST_ALIAS_TO_HOSTS.keys()),
        default="both",
    )
    user_events_parser.add_argument(
        "--after",
        help="ISO date (YYYY-MM-DD). Returns events after that date. Defaults to today.",
    )

    return parser


def build_command_dispatch_table():
    return {
        "mr-view": command_merge_request_view,
        "mr-create": command_merge_request_create,
        "mr-update": command_merge_request_update,
        "mr-changes": command_merge_request_changes,
        "mr-discussions": command_merge_request_discussions,
        "mr-close": command_merge_request_close,
        "mr-merge": command_merge_request_merge,
        "pipelines": command_pipelines,
        "pipeline-jobs": command_pipeline_jobs,
        "delete-branch": command_delete_branch,
        "user-events": command_user_events,
    }


def main():
    parser = build_argument_parser()
    args = parser.parse_args()
    dispatch_table = build_command_dispatch_table()
    if args.command in COMMANDS_THAT_DO_NOT_REQUIRE_GIT_REPO_CONTEXT:
        dispatch_table[args.command](args, None, None, None)
        return
    remote_url = resolve_git_remote_url()
    host = resolve_gitlab_host_from_remote_url(remote_url)
    project = resolve_project_path_from_remote_url(remote_url)
    token = resolve_gitlab_token(host)
    dispatch_table[args.command](args, token, project, host)


if __name__ == "__main__":
    main()
