import argparse
import sys
import urllib.error

import runtime_credentials
import user_account_operations


def build_context():
    return user_account_operations.ArrUsersContext(
        jellyfin_base_url=runtime_credentials.jellyfin_base_url(),
        jellyfin_api_key=runtime_credentials.read_jellyfin_api_key(),
        jellyseerr_base_url=runtime_credentials.jellyseerr_base_url(),
        jellyseerr_api_key=runtime_credentials.read_jellyseerr_api_key(),
    )


def print_accounts(accounts):
    for account in accounts:
        role = "admin" if account["is_administrator"] else "friend"
        state = "disabled" if account["is_disabled"] else "enabled"
        requests_state = (
            "jellyseerr" if account["jellyseerr_user_id"] else "no-jellyseerr"
        )
        print(f"{account['username']}\t{role}\t{state}\t{requests_state}")


def run_list(context, _arguments):
    print_accounts(user_account_operations.list_accounts(context))


def run_create(context, arguments):
    created = user_account_operations.create_friend_account(
        context, arguments.username, arguments.password
    )
    print(f"username: {created['username']}")
    print(f"password: {created['password']}")
    print(f"jellyfin: {created['jellyfin_user_id']}")
    print(f"jellyseerr: {created['jellyseerr_user_id'] or 'import pending'}")


def run_delete(context, arguments):
    deleted = user_account_operations.delete_friend_account(context, arguments.username)
    print(f"deleted {deleted['username']}")


def run_reset_password(context, arguments):
    reset = user_account_operations.reset_friend_password(
        context, arguments.username, arguments.password
    )
    print(f"username: {reset['username']}")
    print(f"password: {reset['password']}")


def run_enable(context, arguments):
    user_account_operations.set_friend_account_enabled(
        context, arguments.username, True
    )
    print(f"enabled {arguments.username}")


def run_disable(context, arguments):
    user_account_operations.set_friend_account_enabled(
        context, arguments.username, False
    )
    print(f"disabled {arguments.username}")


def build_argument_parser():
    parser = argparse.ArgumentParser(
        prog="arr-users",
        description="Manage Jellyfin friend accounts and their Jellyseerr access",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    subparsers.add_parser("list", help="List every account and its Jellyseerr state")

    create_parser = subparsers.add_parser("create", help="Create a friend account")
    create_parser.add_argument("username")
    create_parser.add_argument("--password", default=None)

    delete_parser = subparsers.add_parser("delete", help="Delete a friend account")
    delete_parser.add_argument("username")

    reset_parser = subparsers.add_parser(
        "reset-password", help="Reset a friend account password"
    )
    reset_parser.add_argument("username")
    reset_parser.add_argument("--password", default=None)

    enable_parser = subparsers.add_parser("enable", help="Re-enable a friend account")
    enable_parser.add_argument("username")

    disable_parser = subparsers.add_parser(
        "disable", help="Disable a friend account without deleting it"
    )
    disable_parser.add_argument("username")

    return parser


COMMAND_HANDLERS = {
    "list": run_list,
    "create": run_create,
    "delete": run_delete,
    "reset-password": run_reset_password,
    "enable": run_enable,
    "disable": run_disable,
}


def main():
    arguments = build_argument_parser().parse_args()
    context = build_context()
    handler = COMMAND_HANDLERS[arguments.command]
    try:
        handler(context, arguments)
    except ValueError as error:
        print(str(error), file=sys.stderr)
        raise SystemExit(1) from error
    except urllib.error.HTTPError as error:
        print(
            f"{error.code} from {error.url}: {error.read().decode(errors='replace')}",
            file=sys.stderr,
        )
        raise SystemExit(1) from error
    except urllib.error.URLError as error:
        print(f"cannot reach media service: {error.reason}", file=sys.stderr)
        raise SystemExit(1) from error


if __name__ == "__main__":
    main()
