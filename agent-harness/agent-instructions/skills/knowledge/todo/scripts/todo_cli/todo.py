import argparse

from api import resolve_api_token
from commands import (
    command_add,
    command_delete,
    command_digest,
    command_done,
    command_list,
    command_projects,
    command_reopen,
    command_update,
)


def build_parser():
    parser = argparse.ArgumentParser(
        prog="todo", description="Manage Lucas's Todoist tasks."
    )
    common = argparse.ArgumentParser(add_help=False)
    common.add_argument(
        "--json", action="store_true", help="Emit raw JSON for machine consumption."
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    add_parser = subparsers.add_parser("add", parents=[common], help="Create a task.")
    add_parser.add_argument("content")
    add_parser.add_argument(
        "--due", help="Natural-language due date, e.g. 'tomorrow 9am', 'every monday'."
    )
    add_parser.add_argument(
        "--priority", type=int, choices=[1, 2, 3, 4], help="1-4, 4 = highest (UI p1)."
    )
    add_parser.add_argument(
        "--label", action="append", help="Label without the @, repeatable."
    )
    add_parser.add_argument("--description", help="Longer note attached to the task.")
    add_parser.add_argument("--project", help="Project name or id (default Inbox).")
    add_parser.set_defaults(handler=command_add)

    list_parser = subparsers.add_parser(
        "list", parents=[common], help="List open tasks."
    )
    list_parser.add_argument(
        "--filter",
        help="Todoist filter query, e.g. 'today | overdue', 'no date', '@work', 'p1'.",
    )
    list_parser.set_defaults(handler=command_list)

    digest_parser = subparsers.add_parser(
        "digest",
        parents=[common],
        help="Overdue + today + someday grouped, for a daily push.",
    )
    digest_parser.set_defaults(handler=command_digest)

    done_parser = subparsers.add_parser(
        "done", parents=[common], help="Complete a task by id."
    )
    done_parser.add_argument("id")
    done_parser.set_defaults(handler=command_done)

    reopen_parser = subparsers.add_parser(
        "reopen", parents=[common], help="Reopen a completed task by id."
    )
    reopen_parser.add_argument("id")
    reopen_parser.set_defaults(handler=command_reopen)

    update_parser = subparsers.add_parser(
        "update", parents=[common], help="Modify a task by id."
    )
    update_parser.add_argument("id")
    update_parser.add_argument("--content")
    update_parser.add_argument("--due")
    update_parser.add_argument("--priority", type=int, choices=[1, 2, 3, 4])
    update_parser.add_argument("--label", action="append")
    update_parser.add_argument("--description")
    update_parser.set_defaults(handler=command_update)

    delete_parser = subparsers.add_parser(
        "delete", parents=[common], help="Delete a task by id."
    )
    delete_parser.add_argument("id")
    delete_parser.set_defaults(handler=command_delete)

    projects_parser = subparsers.add_parser(
        "projects", parents=[common], help="List projects and their ids."
    )
    projects_parser.set_defaults(handler=command_projects)

    return parser


def main():
    arguments = build_parser().parse_args()
    arguments.handler(arguments, resolve_api_token())


if __name__ == "__main__":
    main()
