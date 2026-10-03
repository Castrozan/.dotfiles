from dataclasses import dataclass
from pathlib import Path
import re
import subprocess
from urllib.parse import urlsplit


@dataclass(frozen=True)
class Repository:
    provider: str
    hostname: str
    project: str

    @property
    def url(self):
        return f"https://{self.hostname}/{self.project}"


def execute(command, directory):
    return subprocess.run(
        command, cwd=directory, capture_output=True, text=True, timeout=30, check=False
    )


def effective_remote(directory):
    branch = execute(["git", "symbolic-ref", "--short", "HEAD"], directory)
    upstream = execute(
        ["git", "config", "--get", f"branch.{branch.stdout.strip()}.remote"], directory
    )
    remote = upstream.stdout.strip() if upstream.returncode == 0 else "origin"
    response = execute(["git", "remote", "get-url", remote], directory)
    if response.returncode != 0 or not response.stdout.strip():
        raise ValueError(
            f"Cannot resolve Git upstream {remote}: {response.stderr.strip()}"
        )
    return response.stdout.strip()


def parse_remote(remote):
    if "://" not in remote:
        match = re.fullmatch(r"(?:[^@/:]+@)?([^/:]+):(.+)", remote)
        if not match:
            raise ValueError("Repository must have a full HTTPS or SSH Git URL")
        hostname, project = match.groups()
    else:
        parsed = urlsplit(remote)
        if parsed.scheme not in {"https", "http", "ssh"} or not parsed.hostname:
            raise ValueError("Repository must have a full HTTPS or SSH Git URL")
        hostname, project = parsed.hostname, parsed.path.lstrip("/")
    project = project.rstrip("/").removesuffix(".git")
    if len(project.split("/")) < 2 or any(
        part in {"", ".", ".."} for part in project.split("/")
    ):
        raise ValueError("Repository URL must include its namespace and project")
    return hostname.lower(), project


def repository_location(remote, directory):
    hostname, project = parse_remote(remote)
    if "://" not in remote or remote.startswith("ssh://"):
        configured = execute(["ssh", "-G", hostname], directory)
        if configured.returncode != 0:
            raise ValueError("Cannot resolve the SSH repository hostname")
        for line in configured.stdout.splitlines():
            key, _, value = line.partition(" ")
            if key == "hostname":
                return value.strip().lower(), project
        raise ValueError("SSH configuration returned no repository hostname")
    return hostname, project


def provider_for_host(hostname, directory):
    if hostname == "github.com":
        return "github"
    if hostname == "gitlab.com":
        return "gitlab"
    configured = execute(
        ["glab", "config", "get", "api_host", "--host", hostname], directory
    )
    if configured.returncode == 0 and configured.stdout.strip() == hostname:
        return "gitlab"
    configured = execute(
        ["gh", "auth", "status", "--hostname", hostname, "--json", "hosts"], directory
    )
    if configured.returncode == 0:
        import json

        if hostname in json.loads(configured.stdout).get("hosts", {}):
            return "github"
    raise ValueError(
        f"Unrecognized Git hosting provider for {hostname}; specify --provider"
    )


def resolve_repository(directory=None, repository=None, provider=None):
    directory = Path(directory or Path.cwd())
    remote = repository or effective_remote(directory)
    if "://" not in remote and ":" not in remote:
        if repository is None:
            raise ValueError("Git remote has no hostname")
        if provider:
            hostname = "github.com" if provider == "github" else "gitlab.com"
        else:
            hostname, _ = repository_location(effective_remote(directory), directory)
        remote = f"https://{hostname}/{remote}"
    hostname, project = repository_location(remote, directory)
    provider = provider or provider_for_host(hostname, directory)
    if provider not in {"github", "gitlab"}:
        raise ValueError(f"Unsupported Git hosting provider: {provider}")
    return Repository(provider, hostname, project)
