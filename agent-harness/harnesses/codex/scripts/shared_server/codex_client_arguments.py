import argparse


NONINTERACTIVE_COMMANDS = {
    "exec",
    "e",
    "review",
    "login",
    "logout",
    "mcp",
    "plugin",
    "mcp-server",
    "app-server",
    "remote-control",
    "app",
    "completion",
    "update",
    "doctor",
    "sandbox",
    "debug",
    "apply",
    "a",
    "queue",
    "archive",
    "delete",
    "migrate-rollouts",
    "unarchive",
    "cloud",
    "exec-server",
    "features",
    "help",
}


def parse_launch_arguments(arguments):
    parser = argparse.ArgumentParser(add_help=False, allow_abbrev=False)
    parser.add_argument("-p", "--profile")
    parser.add_argument("-c", "--config", action="append", default=[])
    for names in [
        ("-C", "--cd"),
        ("-m", "--model"),
        ("-i", "--image"),
        ("-s", "--sandbox"),
        ("-a", "--ask-for-approval"),
        ("--add-dir",),
        ("--local-provider",),
        ("--enable",),
        ("--disable",),
        ("--remote",),
        ("--remote-auth-token-env",),
    ]:
        parser.add_argument(*names)
    parser.add_argument("command", nargs="?")
    return parser.parse_known_args(arguments)[0]
