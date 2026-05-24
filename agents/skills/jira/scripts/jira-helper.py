#!/usr/bin/env python3
import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from jira_helper_authentication import (  # noqa: E402, F401
    JIRA_API_TOKEN_ENVIRONMENT_VARIABLE_NAME,
    JIRA_API_TOKEN_SECRET_FILE_PATH,
    load_jira_api_token_into_environment_if_missing,
)
from jira_helper_issue_commands import (  # noqa: E402, F401
    add_comment,
    create_issue,
    edit_issue,
    list_issues,
    log_work,
    move_issue,
    my_issues,
    open_in_browser,
    view_issue,
)
from jira_helper_sprint_commands import list_sprints  # noqa: E402, F401
from jira_helper_subprocess_runner import run_jira_command  # noqa: E402, F401


def build_argument_parser():
    parser = argparse.ArgumentParser(description="Jira helper for common operations")
    subparsers = parser.add_subparsers(dest="command", required=True)

    view_parser = subparsers.add_parser("view")
    view_parser.add_argument("issue_key")

    list_parser = subparsers.add_parser("list")
    list_parser.add_argument("--project")
    list_parser.add_argument("--status")
    list_parser.add_argument("--type")
    list_parser.add_argument("--assignee")
    list_parser.add_argument("--label")
    list_parser.add_argument("--jql")
    list_parser.add_argument("--columns")

    create_parser = subparsers.add_parser("create")
    create_parser.add_argument("--summary", required=True)
    create_parser.add_argument("--type", default="Task")
    create_parser.add_argument("--description")
    create_parser.add_argument("--assignee")
    create_parser.add_argument("--priority")
    create_parser.add_argument("--labels")
    create_parser.add_argument("--parent")

    move_parser = subparsers.add_parser("move")
    move_parser.add_argument("issue_key")
    move_parser.add_argument("target_status")
    move_parser.add_argument("--comment")
    move_parser.add_argument("--assignee")

    edit_parser = subparsers.add_parser("edit")
    edit_parser.add_argument("issue_key")
    edit_parser.add_argument("--summary")
    edit_parser.add_argument("--description")
    edit_parser.add_argument("--assignee")
    edit_parser.add_argument("--labels")
    edit_parser.add_argument("--priority")

    comment_parser = subparsers.add_parser("comment")
    comment_parser.add_argument("issue_key")
    comment_parser.add_argument("body")

    subparsers.add_parser("sprints")
    subparsers.add_parser("current-sprint")

    worklog_parser = subparsers.add_parser("log-work")
    worklog_parser.add_argument("issue_key")
    worklog_parser.add_argument("time_spent")
    worklog_parser.add_argument("--comment")

    open_parser = subparsers.add_parser("open")
    open_parser.add_argument("issue_key")

    my_issues_parser = subparsers.add_parser("my-issues")
    my_issues_parser.add_argument("--status")

    return parser


def dispatch_command(args):
    if args.command == "view":
        view_issue(args.issue_key)
    elif args.command == "list":
        list_issues(
            project=args.project,
            status=args.status,
            issue_type=args.type,
            assignee=args.assignee,
            label=args.label,
            jql_query=args.jql,
            columns=args.columns,
        )
    elif args.command == "create":
        create_issue(
            summary=args.summary,
            issue_type=args.type,
            description=args.description,
            assignee=args.assignee,
            priority=args.priority,
            labels=args.labels,
            parent=args.parent,
        )
    elif args.command == "move":
        move_issue(
            args.issue_key,
            args.target_status,
            comment=args.comment,
            assignee=args.assignee,
        )
    elif args.command == "edit":
        edit_issue(
            args.issue_key,
            summary=args.summary,
            description=args.description,
            assignee=args.assignee,
            labels=args.labels,
            priority=args.priority,
        )
    elif args.command == "comment":
        add_comment(args.issue_key, args.body)
    elif args.command == "sprints":
        list_sprints()
    elif args.command == "current-sprint":
        list_sprints(current_only=True)
    elif args.command == "log-work":
        log_work(args.issue_key, args.time_spent, comment=args.comment)
    elif args.command == "open":
        open_in_browser(args.issue_key)
    elif args.command == "my-issues":
        my_issues(status=args.status)


def main():
    load_jira_api_token_into_environment_if_missing()
    parser = build_argument_parser()
    args = parser.parse_args()
    dispatch_command(args)


if __name__ == "__main__":
    main()
