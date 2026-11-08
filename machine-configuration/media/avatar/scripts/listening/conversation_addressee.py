import contextlib
import dataclasses
import fcntl
import json
import os

ADDRESSEE_FILE = "addressee.json"
LOCK_FILE = ".addressee.lock"


@dataclasses.dataclass(frozen=True)
class Addressee:
    pane: str
    servant: str
    heard_through: int


@contextlib.contextmanager
def exclusive(directory):
    directory.mkdir(mode=0o700, parents=True, exist_ok=True)
    descriptor = os.open(directory / LOCK_FILE, os.O_RDWR | os.O_CREAT, 0o600)
    with os.fdopen(descriptor) as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        yield


def current(directory):
    path = directory / ADDRESSEE_FILE
    if not path.exists():
        return None
    return Addressee(**json.loads(path.read_text()))


def write(directory, addressee):
    staged = directory / f".{ADDRESSEE_FILE}"
    descriptor = os.open(staged, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    with os.fdopen(descriptor, "w") as output:
        json.dump(dataclasses.asdict(addressee), output)
    os.replace(staged, directory / ADDRESSEE_FILE)


def hand_to(directory, addressee):
    with exclusive(directory):
        write(directory, addressee)


def forget(directory):
    with exclusive(directory):
        (directory / ADDRESSEE_FILE).unlink(missing_ok=True)


def addresses(directory, pane):
    addressee = current(directory)
    return addressee is None or pane is None or addressee.pane == pane
