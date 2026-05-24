"""Resolve GitLab host, project path, and API token from environment and agenix secrets."""

import os
import subprocess
import sys
from pathlib import Path

GITLAB_HOST_COATES = "git.coates.io"
GITLAB_HOST_PUBLIC = "gitlab.com"

GITLAB_TOKEN_ENVIRONMENT_VARIABLE_NAME_BY_HOST = {
    GITLAB_HOST_COATES: "GITLAB_TOKEN",
    GITLAB_HOST_PUBLIC: "GITLAB_COM_TOKEN",
}

GITLAB_TOKEN_SECRET_FILE_PATH_BY_HOST = {
    GITLAB_HOST_COATES: Path.home() / ".secrets" / "glab-token",
    GITLAB_HOST_PUBLIC: Path.home() / ".secrets" / "gitlab-com-token",
}


def resolve_git_remote_url():
    result = subprocess.run(
        ["git", "remote", "get-url", "origin"],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        print("Error: not a git repository or no origin remote", file=sys.stderr)
        sys.exit(1)
    return result.stdout.strip()


def resolve_gitlab_host_from_remote_url(remote_url):
    if remote_url.startswith("git@"):
        host = remote_url.split("@", 1)[1].split(":", 1)[0]
    elif remote_url.startswith("https://") or remote_url.startswith("http://"):
        host = remote_url.split("/")[2]
    else:
        print(f"Error: unrecognized remote URL format: {remote_url}", file=sys.stderr)
        sys.exit(1)

    if host not in GITLAB_TOKEN_SECRET_FILE_PATH_BY_HOST:
        print(
            f"Error: unsupported GitLab host '{host}'. "
            f"Known hosts: {sorted(GITLAB_TOKEN_SECRET_FILE_PATH_BY_HOST.keys())}",
            file=sys.stderr,
        )
        sys.exit(1)

    return host


def resolve_project_path_from_remote_url(remote_url):
    if remote_url.startswith("git@"):
        path = remote_url.split(":", 1)[1]
    elif remote_url.startswith("https://") or remote_url.startswith("http://"):
        path = "/".join(remote_url.split("/")[3:])
    else:
        print(f"Error: unrecognized remote URL format: {remote_url}", file=sys.stderr)
        sys.exit(1)

    if path.endswith(".git"):
        path = path[:-4]

    return path


def resolve_gitlab_token(host):
    environment_variable_name = GITLAB_TOKEN_ENVIRONMENT_VARIABLE_NAME_BY_HOST[host]
    secret_file_path = GITLAB_TOKEN_SECRET_FILE_PATH_BY_HOST[host]

    token = os.environ.get(environment_variable_name)
    if token:
        return token

    if secret_file_path.is_file():
        token = secret_file_path.read_text().strip()
        os.environ[environment_variable_name] = token
        return token

    print(
        f"Error: {environment_variable_name} not set and "
        f"{secret_file_path} not found. "
        "Run rebuild to deploy agenix secrets.",
        file=sys.stderr,
    )
    sys.exit(1)
