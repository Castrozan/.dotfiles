import enum
import json
import os
import subprocess

import listener
import user_units

LISTENER_SERVICE = "avatar-listener.service"
CONFIGURATION_FILE = "listener.json"
SYSTEMCTL_TIMEOUT_SECONDS = 120


class ListenerPurpose(enum.StrEnum):
    CONVERSATION = "conversation"
    MEETING = "meeting"


def systemctl(*arguments):
    subprocess.run(
        ["systemctl", "--user", *arguments],
        check=True,
        timeout=SYSTEMCTL_TIMEOUT_SECONDS,
    )


def begin_listening(directory, purpose, sources, **settings):
    directory.mkdir(mode=0o700, parents=True, exist_ok=True)
    systemctl("stop", LISTENER_SERVICE)
    (directory / "transcript.jsonl").unlink(missing_ok=True)
    (directory / listener.EMBEDDINGS_FILE).unlink(missing_ok=True)
    (directory / listener.HEARD_FILE).unlink(missing_ok=True)
    configuration = directory / CONFIGURATION_FILE
    descriptor = os.open(configuration, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    with os.fdopen(descriptor, "w") as output:
        json.dump({"purpose": purpose, "sources": sources, **settings}, output)
    systemctl("start", LISTENER_SERVICE)


def stop_listening():
    systemctl("stop", LISTENER_SERVICE)


def listening():
    return user_units.unit_active(LISTENER_SERVICE)


def read_configuration(directory):
    configuration = directory / CONFIGURATION_FILE
    if not configuration.exists():
        return {}
    return json.loads(configuration.read_text())


def configured_sources(directory):
    return read_configuration(directory).get("sources", {})


def configured_purpose(directory):
    return read_configuration(directory).get("purpose")


def live_purpose(directory):
    if not listening():
        return None
    configured = configured_purpose(directory)
    return ListenerPurpose(configured) if configured in ListenerPurpose else None
