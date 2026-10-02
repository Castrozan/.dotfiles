import json
import os
import sys
import tempfile
import time
from pathlib import Path


def read_host_token(token_file: Path, timeout_seconds: float = 30.0) -> str:
    deadline = time.monotonic() + timeout_seconds
    while True:
        try:
            token = token_file.read_text(encoding="utf-8").strip()
        except FileNotFoundError:
            token = ""
        if token:
            return token
        if time.monotonic() >= deadline:
            raise TimeoutError(f"GitLab credential did not materialize: {token_file}")
        time.sleep(0.5)


def write_configuration(source: Path, destination: Path) -> None:
    configuration = json.loads(source.read_text(encoding="utf-8"))
    for host_configuration in configuration["hosts"].values():
        token_file = host_configuration.pop("token_file", None)
        if token_file is not None:
            host_configuration["token"] = read_host_token(Path(token_file))

    destination.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary_name = tempfile.mkstemp(dir=destination.parent)
    temporary_path = Path(temporary_name)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as configuration_file:
            json.dump(configuration, configuration_file, indent=2)
            configuration_file.write("\n")
        temporary_path.replace(destination)
    finally:
        temporary_path.unlink(missing_ok=True)


if __name__ == "__main__":
    write_configuration(Path(sys.argv[1]), Path(sys.argv[2]))
