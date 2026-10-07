import os
import subprocess
from pathlib import Path

from shorts_store import read_document


def main():
    configuration = read_document(Path.home() / ".pinchtab/config.json")
    environment = dict(
        os.environ,
        PINCHTAB_TOKEN=configuration["server"]["token"],
        PINCHTAB_CONFIG=os.environ["SHORTS_BROWSER_CONFIGURATION"],
    )
    binary = os.environ["SHORTS_PINCHTAB"]
    subprocess.run(
        [binary, "config", "validate"],
        env=environment,
        check=True,
        capture_output=True,
    )
    os.execve(binary, [binary, "server"], environment)


if __name__ == "__main__":
    main()
