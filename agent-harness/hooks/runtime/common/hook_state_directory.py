import os
from pathlib import Path


def hook_state_directory() -> Path:
    state_home = Path(os.environ.get("XDG_STATE_HOME") or Path.home() / ".local/state")
    directory = state_home / "agent-hooks"
    directory.mkdir(mode=0o700, parents=True, exist_ok=True)
    if directory.is_symlink() or directory.stat().st_uid != os.getuid():
        raise PermissionError(
            f"hook state directory is not privately owned: {directory}"
        )
    directory.chmod(0o700)
    return directory
