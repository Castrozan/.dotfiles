import json
import os
import subprocess
import sys
from pathlib import Path

from shorts_browser_pages.ownership import BrowserPages
from shorts_store import read_document
from shorts_browser_upload import upload_video


BROWSER_COMMANDS = frozenset(
    "nav snap click fill type upload wait eval text tab health screenshot close press "
    "record set capture console errors scroll select attr box value visible find "
    "handoff handoff-status resume title url focus reload back forward keyboard".split()
)


def authorized_instance(instance, configuration):
    expected = {
        "profileId": configuration["browser_profile_id"],
        "profileName": configuration["browser_profile"],
        "status": "running",
        "url": "http://127.0.0.1:9868",
    }
    return all(instance.get(field) == value for field, value in expected.items())


def browser_instance(configuration):
    result = subprocess.run(
        [
            os.environ["SHORTS_PINCHTAB"],
            "--server",
            "http://127.0.0.1:9867",
            "instances",
            "--json",
        ],
        capture_output=True,
        text=True,
        timeout=15,
    )
    if result.returncode:
        raise ValueError("The dedicated Shorts browser is unavailable")
    instances = json.loads(result.stdout)
    matches = [
        instance
        for instance in instances
        if authorized_instance(instance, configuration)
    ]
    if len(matches) != 1:
        raise ValueError("The exact logged-in Shorts profile is not running")
    return matches[0]


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
    return value == "--server" or value.startswith("--server=")


def browser_arguments(arguments, configuration):
    validate_browser_arguments(arguments)
    instance = browser_instance(configuration)
    return [os.environ["SHORTS_PINCHTAB"], "--server", instance["url"], *arguments]


def browser_pages(directory, configuration):
    instance = browser_instance(configuration)
    return BrowserPages(
        directory.parent.parent,
        directory.name,
        [os.environ["SHORTS_PINCHTAB"], "--server", instance["url"]],
        instance["id"],
    )


def execute_browser(arguments, configuration, command):
    if arguments[0] == "upload":
        print(
            json.dumps(
                upload_video(
                    arguments[1:], command[2], configuration["browser_profile_id"]
                )
            )
        )
        return 0
    return subprocess.run([*command, *arguments]).returncode


def execute_scoped_browser(arguments, configuration, command, directory, instance):
    pages = BrowserPages(
        directory.parent.parent, directory.name, command, instance["id"]
    )
    with pages.lock():
        if arguments in (["tab"], ["tab", "--json"]):
            print(json.dumps(pages.tabs()))
            return 0
        scoped = pages.arguments(arguments)
        returncode = execute_browser(scoped, configuration, command)
        forget_closed_page(pages, scoped, returncode)
        return returncode


def forget_closed_page(pages, arguments, returncode):
    if returncode != 0:
        return
    if arguments[0] == "close":
        pages.forget(arguments[1])
        return
    if arguments[:2] == ["tab", "close"]:
        pages.forget(arguments[2])


def main():
    configuration = read_document(os.environ["SHORTS_CONFIGURATION"])
    arguments = sys.argv[1:]
    validate_browser_arguments(arguments)
    instance = browser_instance(configuration)
    command = [os.environ["SHORTS_PINCHTAB"], "--server", instance["url"]]
    directory = os.environ.get("SHORTS_BROWSER_RUN")
    if directory is None or arguments[1:] in (["--help"], ["-h"]):
        return execute_browser(arguments, configuration, command)
    return execute_scoped_browser(
        arguments, configuration, command, Path(directory), instance
    )


if __name__ == "__main__":
    sys.exit(main())
