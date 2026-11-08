import enum
import json
import os
import subprocess

import conversation_addressee
import listener
import listener_runtime
from listener_runtime import LISTENER_SERVICE, LIVE_SERVICE

CONFIGURATION_FILE = "listener.json"
SYSTEMCTL_TIMEOUT_SECONDS = 120


class ListenerPurpose(enum.StrEnum):
    CONVERSATION = "conversation"
    MEETING = "meeting"
    LIVE = "live"


SERVICE_BY_PURPOSE = {
    ListenerPurpose.CONVERSATION: LISTENER_SERVICE,
    ListenerPurpose.MEETING: LISTENER_SERVICE,
    ListenerPurpose.LIVE: LIVE_SERVICE,
}


def systemctl(*arguments):
    subprocess.run(
        ["systemctl", "--user", *arguments],
        check=True,
        timeout=SYSTEMCTL_TIMEOUT_SECONDS,
    )


def begin_listening(directory, purpose, sources, **settings):
    directory.mkdir(mode=0o700, parents=True, exist_ok=True)
    stop_listening()
    (directory / "transcript.jsonl").unlink(missing_ok=True)
    (directory / listener.EMBEDDINGS_FILE).unlink(missing_ok=True)
    (directory / listener.HEARD_FILE).unlink(missing_ok=True)
    conversation_addressee.forget(directory)
    configuration = directory / CONFIGURATION_FILE
    descriptor = os.open(configuration, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    with os.fdopen(descriptor, "w") as output:
        json.dump({"purpose": purpose, "sources": sources, **settings}, output)
    systemctl("start", SERVICE_BY_PURPOSE[purpose])


def stop_listening():
    for service in listener_runtime.capturing_services():
        systemctl("stop", service)


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
    if not listener_runtime.listening():
        return None
    configured = configured_purpose(directory)
    return ListenerPurpose(configured) if configured in ListenerPurpose else None
