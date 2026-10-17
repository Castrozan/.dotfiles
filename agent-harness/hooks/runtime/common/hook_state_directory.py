import os


def hook_state_directory() -> str:
    state_home = os.environ.get("XDG_STATE_HOME") or os.path.expanduser(
        "~/.local/state"
    )
    directory = os.path.join(state_home, "agent-hooks")
    os.makedirs(directory, mode=0o700, exist_ok=True)
    if os.path.islink(directory) or os.stat(directory).st_uid != os.getuid():
        raise PermissionError(
            f"hook state directory is not privately owned: {directory}"
        )
    os.chmod(directory, 0o700)
    return directory
