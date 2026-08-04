import os
import subprocess
import sys
from pathlib import Path

REPOSITORY_LOCAL_HOOK_NAME = "prepare-commit-msg"
SKIPPED_MESSAGE_SOURCES = frozenset({"merge", "squash"})
PROVENANCE_ENABLED_CONFIGURATION_KEY = "agent.provenance.enabled"
DEFAULT_COMMENT_CHARACTER = "#"


def comment_character_for_repository() -> str:
    configuration_read = subprocess.run(
        ["git", "config", "--get", "core.commentChar"],
        capture_output=True,
        text=True,
        check=False,
    )
    configured_comment_character = configuration_read.stdout.strip()
    if not configured_comment_character or configured_comment_character == "auto":
        return DEFAULT_COMMENT_CHARACTER
    return configured_comment_character


def message_file_carries_a_message(message_file_path: Path) -> bool:
    comment_character = comment_character_for_repository()
    try:
        message_lines = message_file_path.read_text(encoding="utf-8").splitlines()
    except OSError:
        return False
    return any(
        message_line.strip() and not message_line.startswith(comment_character)
        for message_line in message_lines
    )


def provenance_is_disabled_for_repository() -> bool:
    configuration_read = subprocess.run(
        ["git", "config", "--get", PROVENANCE_ENABLED_CONFIGURATION_KEY],
        capture_output=True,
        text=True,
        check=False,
    )
    return configuration_read.stdout.strip().lower() in {"false", "0", "no", "off"}


def repository_local_hook_path() -> Path | None:
    common_directory_read = subprocess.run(
        ["git", "rev-parse", "--git-common-dir"],
        capture_output=True,
        text=True,
        check=False,
    )
    if common_directory_read.returncode != 0:
        return None
    common_directory = common_directory_read.stdout.strip()
    if not common_directory:
        return None
    hook_path = Path(common_directory).resolve() / "hooks" / REPOSITORY_LOCAL_HOOK_NAME
    return hook_path if os.access(hook_path, os.X_OK) else None


def run_repository_local_hook(hook_path: Path, hook_arguments: list[str]) -> int:
    return subprocess.run([str(hook_path), *hook_arguments], check=False).returncode


def write_trailers_without_blocking_the_commit(message_file_path: Path) -> None:
    try:
        from agent_commit_provenance.commit_trailers import (
            trailers_for_identity,
            write_trailers_into_message_file,
        )
        from agent_commit_provenance.session_identity import (
            resolve_agent_session_identity,
        )

        identity = resolve_agent_session_identity(os.environ, os.getpid(), Path.cwd())
        if identity is None:
            return
        write_trailers_into_message_file(
            message_file_path, trailers_for_identity(identity)
        )
    except Exception as unexpected_failure:
        print(f"agent commit provenance skipped: {unexpected_failure}", file=sys.stderr)


def main(hook_arguments: list[str]) -> int:
    if not hook_arguments:
        return 0
    local_hook_path = repository_local_hook_path()
    if local_hook_path is not None:
        local_hook_status = run_repository_local_hook(local_hook_path, hook_arguments)
        if local_hook_status != 0:
            return local_hook_status
    message_source = hook_arguments[1] if len(hook_arguments) > 1 else ""
    if message_source in SKIPPED_MESSAGE_SOURCES:
        return 0
    if provenance_is_disabled_for_repository():
        return 0
    message_file_path = Path(hook_arguments[0])
    if not message_file_carries_a_message(message_file_path):
        return 0
    write_trailers_without_blocking_the_commit(message_file_path)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
