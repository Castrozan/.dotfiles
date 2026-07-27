import argparse


def build_argument_parser():
    parser = argparse.ArgumentParser(
        prog="arr-users",
        description="Manage Jellyfin friend accounts and their Jellyseerr access",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    subparsers.add_parser("list", help="List every account and its Jellyseerr state")

    subparsers.add_parser(
        "sync",
        help="Create any missing declared Jellyfin library and re-apply the private-library boundary to every friend",
    )

    subparsers.add_parser(
        "sync-request-routing",
        help="Re-apply the Jellyseerr override rules that send every private-requests account request to a private root folder",
    )

    create_parser = subparsers.add_parser("create", help="Create a friend account")
    create_parser.add_argument("username")
    create_parser.add_argument("--password", default=None)
    create_parser.add_argument("--email", default=None)

    set_email_parser = subparsers.add_parser(
        "set-email", help="Set a friend's email so request notifications reach them"
    )
    set_email_parser.add_argument("username")
    set_email_parser.add_argument("email")

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
