import os
import subprocess
import sys
from pathlib import Path

DEVELOPMENT_MODULE_DIRECTORY = Path(__file__).resolve().parents[2]
REPOSITORY_ROOT_DIRECTORY = DEVELOPMENT_MODULE_DIRECTORY.parents[1]
HOOK_ENTRYPOINT_PATH = (
    DEVELOPMENT_MODULE_DIRECTORY
    / "scripts"
    / "record_agent_commit_provenance_trailers.py"
)
PROVENANCE_SCRIPTS_DIRECTORY = HOOK_ENTRYPOINT_PATH.parent
AGENT_SESSION_SCRIPTS_DIRECTORY = (
    REPOSITORY_ROOT_DIRECTORY / "agent-harness" / "session-control"
)

RECORDED_SESSION_IDENTIFIER = "11111111-2222-3333-4444-555555555555"
AMENDED_SESSION_IDENTIFIER = "99999999-2222-3333-4444-555555555555"


def agent_session_environment(session_identifier=RECORDED_SESSION_IDENTIFIER):
    return {
        **os.environ,
        "PYTHONPATH": os.pathsep.join(
            [str(PROVENANCE_SCRIPTS_DIRECTORY), str(AGENT_SESSION_SCRIPTS_DIRECTORY)]
        ),
        "CLAUDE_CODE_SESSION_ID": session_identifier,
        "CLAWDE_AGENT_NAME": "",
        "AGENT_COMMIT_PROVENANCE_MACHINE": "testmachine",
        "GIT_EDITOR": "true",
    }


def run_git(repository_directory: Path, *arguments: str, environment=None):
    return subprocess.run(
        ["git", "-C", str(repository_directory), *arguments],
        capture_output=True,
        text=True,
        check=False,
        env=environment if environment is not None else agent_session_environment(),
    )


def repository_with_the_hook_installed(tmp_path: Path) -> Path:
    hooks_directory = tmp_path / "hooks"
    hooks_directory.mkdir()
    hook_path = hooks_directory / "prepare-commit-msg"
    hook_path.write_text(
        f'#!/bin/sh\nexec {sys.executable} {HOOK_ENTRYPOINT_PATH} "$@"\n',
        encoding="utf-8",
    )
    hook_path.chmod(0o755)
    repository_directory = tmp_path / "repository"
    repository_directory.mkdir()
    run_git(repository_directory, "init", "--initial-branch=main")
    run_git(repository_directory, "config", "core.hooksPath", str(hooks_directory))
    run_git(repository_directory, "config", "user.email", "test@example.com")
    run_git(repository_directory, "config", "user.name", "test")
    return repository_directory


def commit_a_change(
    repository_directory: Path, file_name: str, message: str, environment=None
):
    (repository_directory / file_name).write_text(file_name, encoding="utf-8")
    run_git(repository_directory, "add", file_name, environment=environment)
    return run_git(
        repository_directory, "commit", "-m", message, environment=environment
    )


def latest_commit_message(repository_directory: Path) -> str:
    return run_git(repository_directory, "log", "-1", "--format=%B").stdout.strip()


def latest_trailer_value(repository_directory: Path, trailer_key: str) -> str:
    return run_git(
        repository_directory,
        "log",
        "-1",
        f"--format=%(trailers:key={trailer_key},valueonly)",
    ).stdout.strip()


def install_repository_local_hook(repository_directory: Path, hook_body: str) -> None:
    local_hook_path = repository_directory / ".git" / "hooks" / "prepare-commit-msg"
    local_hook_path.parent.mkdir(parents=True, exist_ok=True)
    local_hook_path.write_text(hook_body, encoding="utf-8")
    local_hook_path.chmod(0o755)
