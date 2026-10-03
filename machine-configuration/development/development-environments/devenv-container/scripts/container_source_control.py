from pathlib import Path


def shared_git_metadata(project, workspace_root, execute_command):
    if not (project.directory / ".git").is_file():
        return []
    result = execute_command(
        [
            "git",
            "-C",
            str(project.directory),
            "rev-parse",
            "--path-format=absolute",
            "--git-common-dir",
        ],
        capture=True,
        timeout=10,
    )
    metadata = Path(result.stdout.strip()).resolve()
    if not metadata.is_relative_to(Path(workspace_root).resolve()):
        raise ValueError(
            "Shared Git metadata must remain inside the configured workspace root"
        )
    return [] if metadata.is_relative_to(project.directory) else [metadata]
