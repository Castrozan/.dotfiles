import dataclasses
import json
import os

ADDRESSEE_FILE = "addressee.json"


@dataclasses.dataclass(frozen=True)
class Addressee:
    pane: str
    servant: str
    heard_through: int


def current(directory):
    path = directory / ADDRESSEE_FILE
    if not path.exists():
        return None
    return Addressee(**json.loads(path.read_text()))


def hand_to(directory, addressee):
    directory.mkdir(mode=0o700, parents=True, exist_ok=True)
    staged = directory / f".{ADDRESSEE_FILE}"
    descriptor = os.open(staged, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    with os.fdopen(descriptor, "w") as output:
        json.dump(dataclasses.asdict(addressee), output)
    os.replace(staged, directory / ADDRESSEE_FILE)


def forget(directory):
    (directory / ADDRESSEE_FILE).unlink(missing_ok=True)


def addresses(directory, pane):
    addressee = current(directory)
    return addressee is None or pane is None or addressee.pane == pane
