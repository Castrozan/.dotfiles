import os
import subprocess
import sys
import time
from pathlib import Path


def read_github_token(token_file: Path, timeout_seconds: float = 30.0) -> str:
    deadline = time.monotonic() + timeout_seconds
    while True:
        try:
            token = token_file.read_text(encoding="utf-8").strip()
        except FileNotFoundError:
            token = ""
        if token:
            return token
        if time.monotonic() >= deadline:
            raise TimeoutError(f"GitHub credential did not materialize: {token_file}")
        time.sleep(0.5)


def deploy_github_authentication(github_command: str, token_file: Path) -> None:
    github_token = read_github_token(token_file)
    environment = os.environ.copy()
    environment.pop("GH_TOKEN", None)
    environment.pop("GITHUB_TOKEN", None)
    existing_credential = subprocess.run(
        [github_command, "auth", "token", "--hostname", "github.com"],
        env=environment,
        capture_output=True,
        text=True,
        timeout=10,
        check=False,
    )
    if (
        existing_credential.returncode == 0
        and existing_credential.stdout.strip() == github_token
    ):
        return
    subprocess.run(
        [
            github_command,
            "auth",
            "login",
            "--hostname",
            "github.com",
            "--git-protocol",
            "ssh",
            "--skip-ssh-key",
            "--with-token",
        ],
        input=github_token + "\n",
        env=environment,
        text=True,
        timeout=30,
        check=True,
    )


if __name__ == "__main__":
    deploy_github_authentication(sys.argv[1], Path(sys.argv[2]))
