import os

from changed_file_paths import collect_changed_file_paths
from hook_dispatch import HandlerResult


def path_has_repository_ancestor(path):
    if os.environ.get("GIT_DIR"):
        return True
    directory = os.path.realpath(os.path.dirname(path))
    while True:
        if os.path.lexists(os.path.join(directory, ".git")):
            return True
        parent = os.path.dirname(directory)
        if parent == directory:
            return False
        directory = parent


def affected_repository_directories(paths):
    from collections import defaultdict
    from pathlib import Path

    from repository_directory_entries import repository_root_for_path

    repositories = defaultdict(set)
    for path in paths:
        absolute_path = Path(path).parent.resolve() / Path(path).name
        repository_root = repository_root_for_path(absolute_path)
        if repository_root is None:
            continue
        for directory in absolute_path.parents:
            if not directory.is_relative_to(repository_root):
                break
            relative = directory.relative_to(repository_root).as_posix()
            repositories[repository_root].add(relative)
    return repositories


def handle(hook_input):
    if hook_input.get("tool_name") not in {
        "Write",
        "Edit",
        "MultiEdit",
        "NotebookEdit",
        "apply_patch",
    }:
        return None
    paths = [
        path
        for path in collect_changed_file_paths(hook_input)
        if path_has_repository_ancestor(path)
    ]
    if not paths:
        return None
    import subprocess

    from directory_entry_policy import directory_entry_violations
    from excluded_repositories import (
        load_excluded_repository_patterns,
        repository_is_excluded,
    )
    from repository_directory_entries import (
        directory_entry_ceilings,
        repository_entry_counts,
    )

    try:
        repositories = affected_repository_directories(paths)
        excluded_repository_patterns = load_excluded_repository_patterns()
        for repository_root, directories in repositories.items():
            if repository_is_excluded(repository_root, excluded_repository_patterns):
                continue
            violations = directory_entry_violations(
                repository_entry_counts(repository_root),
                directory_entry_ceilings(repository_root),
                directories,
            )
            if violations:
                reason = f"Repository {repository_root}: " + violations[0].describe()
                return HandlerResult(
                    decision="block", reason=reason, system_message=f"BLOCKED: {reason}"
                )
    except (OSError, ValueError, subprocess.SubprocessError) as error:
        reason = f"Directory entry check could not complete: {error}"
        return HandlerResult(decision="block", reason=reason, system_message=reason)
    return None
