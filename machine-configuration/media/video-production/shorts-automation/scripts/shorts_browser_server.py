import os
import signal
from pathlib import Path

from shorts_store import read_document, write_document


def runtime_path():
    state = Path(os.environ.get("XDG_STATE_HOME", Path.home() / ".local/state"))
    return state / "shorts-production/browser.json"


def stop(number, frame):
    raise SystemExit(128 + number)


def main():
    configuration = read_document(os.environ["SHORTS_CONFIGURATION"])
    scope = os.environ["OPENCLI_JOB_SCOPE"]
    if Path(scope).name != configuration["browser_profile"]:
        raise ValueError("The exact Shorts profile must own the browser job")
    for number in (signal.SIGTERM, signal.SIGINT, signal.SIGHUP):
        signal.signal(number, stop)
    path = runtime_path()
    path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    write_document(
        path,
        {
            "id": os.environ["OPENCLI_JOB_IDENTIFIER"],
            "profileName": configuration["browser_profile"],
            "scope": scope,
            "pid": os.getpid(),
        },
    )
    try:
        while True:
            signal.pause()
    finally:
        path.unlink(missing_ok=True)


if __name__ == "__main__":
    main()
