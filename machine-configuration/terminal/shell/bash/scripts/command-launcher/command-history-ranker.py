import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path


def normalize_history(source, destination):
    timestamp_seen = False
    for line in source:
        if re.fullmatch(r"#[0-9]+\n?", line):
            timestamp_seen = True
        if not timestamp_seen:
            destination.write("#0\n")
        destination.write(line)


def main():
    try:
        history_file = Path(os.environ["HISTFILE"])
        with tempfile.TemporaryDirectory(prefix="command-history-") as directory:
            normalized_history = Path(directory) / "history"
            with (
                history_file.open() as source,
                normalized_history.open("w") as destination,
            ):
                normalize_history(source, destination)
            environment = os.environ | {"HISTFILE": str(normalized_history)}
            return subprocess.run(sys.argv[1:], env=environment, check=False).returncode
    except (OSError, KeyError) as error:
        print(f"cx: cannot read command history: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
