import json
import os
import subprocess
import sys

from shorts_store import read_document


BROWSER_COMMANDS = frozenset(
    "nav snap click fill type upload wait eval text tab health screenshot close press "
    "record set capture console errors scroll select attr box value visible find "
    "handoff handoff-status resume title url focus reload back forward keyboard".split()
)


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
        if instance.get("profileId") == configuration["browser_profile_id"]
        and instance.get("profileName") == configuration["browser_profile"]
        and instance.get("status") == "running"
        and instance.get("url") == "http://127.0.0.1:9868"
    ]
    if len(matches) != 1:
        raise ValueError("The exact logged-in Shorts profile is not running")
    return matches[0]


def browser_arguments(arguments, configuration):
    if (
        not arguments
        or arguments[0] not in BROWSER_COMMANDS
        or any(
            value == "--server" or value.startswith("--server=") for value in arguments
        )
    ):
        raise ValueError(
            "Use browser actions only; the Shorts profile cannot be changed"
        )
    instance = browser_instance(configuration)
    return [os.environ["SHORTS_PINCHTAB"], "--server", instance["url"], *arguments]


def main():
    configuration = read_document(os.environ["SHORTS_CONFIGURATION"])
    arguments = browser_arguments(sys.argv[1:], configuration)
    os.execv(arguments[0], arguments)


if __name__ == "__main__":
    main()
