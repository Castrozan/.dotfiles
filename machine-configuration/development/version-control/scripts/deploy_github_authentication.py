import os
import subprocess
import sys
import time
from pathlib import Path

import yaml


GITHUB_HOSTNAME = "github.com"
MALFORMED_GITHUB_CONFIGURATION = "GitHub CLI authentication file is malformed"


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


def read_github_file_credential(credential_file: Path) -> str | None:
    try:
        configuration = yaml.safe_load(credential_file.read_text(encoding="utf-8"))
    except FileNotFoundError:
        return None
    except yaml.YAMLError:
        raise ValueError(MALFORMED_GITHUB_CONFIGURATION) from None
    if configuration is None:
        return None
    if not isinstance(configuration, dict):
        raise ValueError(MALFORMED_GITHUB_CONFIGURATION)
    github_configuration = configuration.get(GITHUB_HOSTNAME, {})
    if not isinstance(github_configuration, dict):
        raise ValueError(MALFORMED_GITHUB_CONFIGURATION)
    return github_configuration.get("oauth_token")


def deploy_github_authentication(
    github_command: str, token_file: Path, credential_file: Path
) -> None:
    github_token = read_github_token(token_file)
    if read_github_file_credential(credential_file) == github_token:
        return
    environment = os.environ.copy()
    environment.pop("GH_TOKEN", None)
    environment.pop("GITHUB_TOKEN", None)
    environment["GH_CONFIG_DIR"] = str(credential_file.parent)
    subprocess.run(
        [
            github_command,
            "auth",
            "login",
            "--hostname",
            GITHUB_HOSTNAME,
            "--git-protocol",
            "ssh",
            "--skip-ssh-key",
            "--insecure-storage",
            "--with-token",
        ],
        input=github_token + "\n",
        env=environment,
        text=True,
        timeout=30,
        check=True,
    )


if __name__ == "__main__":
    deploy_github_authentication(sys.argv[1], Path(sys.argv[2]), Path(sys.argv[3]))
