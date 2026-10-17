import json
import os
import sys


def public_adapter(arguments):
    if len(arguments) < 2:
        return False
    with open(os.environ["OPENCLI_MANIFEST"]) as source:
        manifest = json.load(source)
    return any(
        [command.get("site"), command.get("name")] == arguments[:2]
        and command.get("browser") is False
        for command in manifest
    )


def requests_help(arguments):
    option_arguments = (
        arguments[: arguments.index("--")] if "--" in arguments else arguments
    )
    return any(value in ("--help", "-h") for value in option_arguments)


def metadata_command(arguments):
    if not arguments or requests_help(arguments):
        return True
    return arguments[0] in (
        "--version",
        "-V",
        "list",
        "completion",
        "--get-completions",
    ) or arguments[:2] in (["adapter", "init"], ["adapter", "check"])


def validate_daemon_command(arguments):
    if arguments[:1] == ["daemon"] and arguments[1:2] not in (
        ["status"],
        ["--help"],
        ["-h"],
    ):
        raise ValueError(
            "The job owns its daemon; use opencli-run instead of daemon lifecycle commands"
        )


def direct_command(arguments):
    return (
        metadata_command(arguments)
        or public_adapter(arguments)
        or os.environ.get("OPENCLI_JOB_SCOPE")
        or arguments[:2] == ["daemon", "status"]
    )


def main():
    arguments = sys.argv[1:]
    validate_daemon_command(arguments)
    if direct_command(arguments):
        os.execv(os.environ["OPENCLI_CLI"], [os.environ["OPENCLI_CLI"], *arguments])
    if arguments[:1] == ["browser"]:
        raise ValueError(
            "Run multi-step browser commands inside opencli-run -- sh -c 'opencli browser ...'"
        )
    runner = os.environ["OPENCLI_JOB_RUNNER"]
    os.execv(runner, [runner, "--", os.environ["OPENCLI_CLI"], *arguments])


if __name__ == "__main__":
    try:
        main()
    except (OSError, ValueError) as error:
        print(f"opencli: {error}", file=sys.stderr)
        sys.exit(1)
