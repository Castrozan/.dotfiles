import argparse
import sys
import time
from pathlib import Path

SECRET_MATERIALIZATION_TIMEOUT_SECONDS = 30.0
SECRET_POLL_INTERVAL_SECONDS = 0.5


def parse_key_value_pair(raw_pair: str) -> tuple[str, str]:
    key, separator, value = raw_pair.partition("=")
    if not separator:
        raise argparse.ArgumentTypeError(f"expected KEY=VALUE, got {raw_pair!r}")
    return key, value


def read_existing_credentials(output_path: Path) -> dict[str, str]:
    if not output_path.exists():
        return {}
    existing_credentials: dict[str, str] = {}
    for line in output_path.read_text(encoding="utf-8").splitlines():
        if "=" not in line or line.lstrip().startswith("#"):
            continue
        key, _, value = line.partition("=")
        existing_credentials[key.strip()] = value
    return existing_credentials


def read_secret_file(secret_file: Path) -> str:
    try:
        return secret_file.read_text(encoding="utf-8").strip()
    except OSError:
        return ""


def read_secret_backed_credentials(
    secret_file_pairs: list[tuple[str, str]],
    timeout_seconds: float = SECRET_MATERIALIZATION_TIMEOUT_SECONDS,
) -> tuple[dict[str, str], list[str]]:
    deadline = time.monotonic() + timeout_seconds
    resolved_credentials: dict[str, str] = {}
    unresolved_credentials: list[str] = []
    for key, secret_path in secret_file_pairs:
        secret_file = Path(secret_path)
        secret_value = read_secret_file(secret_file)
        while not secret_value and time.monotonic() < deadline:
            time.sleep(SECRET_POLL_INTERVAL_SECONDS)
            secret_value = read_secret_file(secret_file)
        if secret_value:
            resolved_credentials[key] = secret_value
        else:
            unresolved_credentials.append(f"{key} ({secret_path})")
    return resolved_credentials, unresolved_credentials


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-path", required=True)
    parser.add_argument(
        "--literal", action="append", type=parse_key_value_pair, default=[]
    )
    parser.add_argument(
        "--from-secret-file", action="append", type=parse_key_value_pair, default=[]
    )
    parser.add_argument(
        "--secret-timeout-seconds",
        type=float,
        default=SECRET_MATERIALIZATION_TIMEOUT_SECONDS,
    )
    arguments = parser.parse_args()

    output_path = Path(arguments.output_path)
    secret_backed_credentials, unresolved_credentials = read_secret_backed_credentials(
        arguments.from_secret_file, arguments.secret_timeout_seconds
    )
    if unresolved_credentials:
        print(
            f"refusing to write a partial {output_path}: waited "
            f"{arguments.secret_timeout_seconds:.0f}s and these secrets never "
            f"materialized: {', '.join(unresolved_credentials)}",
            file=sys.stderr,
        )
        return 1

    credentials = {
        **read_existing_credentials(output_path),
        **dict(arguments.literal),
        **secret_backed_credentials,
    }

    rendered_credentials = "".join(
        f"{key}={value}\n" for key, value in sorted(credentials.items())
    )
    if output_path.exists() and output_path.read_text(encoding="utf-8") == (
        rendered_credentials
    ):
        output_path.chmod(0o600)
        return 0

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(rendered_credentials, encoding="utf-8")
    output_path.chmod(0o600)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
