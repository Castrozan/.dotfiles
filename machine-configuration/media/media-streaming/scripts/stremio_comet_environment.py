import os
import sys
import xml.etree.ElementTree as element_tree
from pathlib import Path


def read_prowlarr_api_key(config_file: Path) -> str:
    api_key = element_tree.parse(config_file).getroot().findtext("ApiKey", "").strip()
    if not api_key:
        raise RuntimeError("Prowlarr API key is missing")
    if "\n" in api_key or "\r" in api_key:
        raise RuntimeError("Prowlarr API key contains an invalid newline")
    return api_key


def write_prowlarr_environment(config_file: Path, environment_file: Path) -> None:
    api_key = read_prowlarr_api_key(config_file)
    flags = os.O_WRONLY | os.O_CREAT | os.O_TRUNC | os.O_CLOEXEC | os.O_NOFOLLOW
    descriptor = os.open(environment_file, flags, 0o600)
    with os.fdopen(descriptor, "w", encoding="utf-8") as destination:
        destination.write(f"PROWLARR_API_KEY={api_key}\n")
    environment_file.chmod(0o600)


def main() -> None:
    if len(sys.argv) != 3:
        raise SystemExit("usage: stremio_comet_environment.py CONFIG OUTPUT")
    write_prowlarr_environment(Path(sys.argv[1]), Path(sys.argv[2]))


if __name__ == "__main__":
    main()
