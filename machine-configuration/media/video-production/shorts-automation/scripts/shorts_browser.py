import json
import os
import subprocess
import sys
from http.client import HTTPConnection, HTTPException
from pathlib import Path

from shorts_browser_pages.ownership import BrowserPages
from shorts_browser_pages.transport import browser_environment
from shorts_browser_upload import upload_video
from shorts_store import read_document

BROWSER_COMMANDS = frozenset(
    "open state click fill type upload wait eval get tab screenshot keys scroll select find back network".split()
)


def browser_instance(configuration):
    from shorts_browser_server import runtime_path

    try:
        instance = read_document(runtime_path())
        validate_profile(instance, configuration)
        os.kill(instance["pid"], 0)
        status = daemon_status()
        if status.get("managedJobId") != instance["id"] or not status.get(
            "extensionConnected"
        ):
            raise ValueError("The exact logged-in Shorts profile is not running")
        return instance
    except (OSError, HTTPException, KeyError) as error:
        raise ValueError("The exact logged-in Shorts profile is not running") from error


def daemon_status():
    connection = HTTPConnection("127.0.0.1", 19825, timeout=3)
    try:
        connection.request("GET", "/status", headers={"X-OpenCLI": "1"})
        return json.load(connection.getresponse())
    finally:
        connection.close()


def validate_profile(instance, configuration):
    expected = (
        Path.home() / ".local/share/opencli/profiles" / configuration["browser_profile"]
    )
    if (
        instance["profileName"] != configuration["browser_profile"]
        or Path(instance["scope"]).resolve() != expected.resolve()
    ):
        raise ValueError("The exact logged-in Shorts profile is not running")


def command_for(instance):
    return [os.environ["SHORTS_OPENCLI"], "browser", "--session", "shorts-production"]


def validate_browser_arguments(arguments):
    if (
        not arguments
        or arguments[0] not in BROWSER_COMMANDS
        or any(server_option(value) for value in arguments)
    ):
        raise ValueError(
            "Use browser actions only; the Shorts profile cannot be changed"
        )


def server_option(value):
    return value in ("--server", "--profile", "--session") or value.startswith(
        ("--server=", "--profile=", "--session=")
    )


def browser_arguments(arguments, configuration):
    validate_browser_arguments(arguments)
    instance = browser_instance(configuration)
    return [*command_for(instance), *arguments]


def browser_pages(directory, configuration):
    instance = browser_instance(configuration)
    return BrowserPages(
        directory.parent.parent,
        directory.name,
        command_for(instance),
        instance["id"],
        instance["scope"],
    )


def execute_browser(arguments, configuration, command, scope):
    if arguments[0] == "upload":
        print(
            json.dumps(upload_video(arguments[1:], command, browser_environment(scope)))
        )
        return 0
    return subprocess.run(
        [*command, *arguments], env=browser_environment(scope)
    ).returncode


def execute_scoped_browser(arguments, configuration, command, directory, instance):
    pages = BrowserPages(
        directory.parent.parent,
        directory.name,
        command,
        instance["id"],
        instance["scope"],
    )
    with pages.lock():
        if arguments == ["tab", "list"]:
            print(json.dumps(pages.tabs()))
            return 0
        scoped = pages.arguments(arguments)
        returncode = execute_browser(
            scoped, configuration, pages.target_command(scoped), instance["scope"]
        )
        forget_closed_page(pages, scoped, returncode)
        return returncode


def forget_closed_page(pages, arguments, returncode):
    if returncode != 0:
        return
    if arguments[:2] == ["tab", "close"]:
        pages.forget(arguments[2])


def main():
    configuration = read_document(os.environ["SHORTS_CONFIGURATION"])
    arguments = sys.argv[1:]
    validate_browser_arguments(arguments)
    instance = browser_instance(configuration)
    command = command_for(instance)
    directory = os.environ.get("SHORTS_BROWSER_RUN")
    if directory is None or arguments[1:] in (["--help"], ["-h"]):
        return execute_browser(arguments, configuration, command, instance["scope"])
    return execute_scoped_browser(
        arguments, configuration, command, Path(directory), instance
    )


if __name__ == "__main__":
    sys.exit(main())
