import os
from pathlib import Path


def agents_directory():
    configured = os.environ.get("CLAWDE_AGENTS_DIRECTORY")
    if configured:
        return Path(configured).expanduser().resolve()
    return (Path.home() / "clawde").resolve()
