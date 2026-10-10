import fcntl
import json
import os
from itertools import islice
from pathlib import Path

from .mail import attempt
from .state import collect, pending


def main():
    os.umask(0o077)
    ledger = Path(os.environ["STATE_DIRECTORY"])
    password = Path(os.environ["CREDENTIALS_DIRECTORY"]) / "smtp-password"
    root = Path("/home/zanoni/clawde/shorts")
    with (ledger / "delivery.lock").open("a") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        collect(root, ledger)
        for path, record in islice(pending(ledger), 2):
            attempt(path, record, password)
            print(
                json.dumps(
                    {
                        "video_id": record["event"]["video_id"],
                        "status": record["status"],
                    }
                ),
                flush=True,
            )


if __name__ == "__main__":
    main()
