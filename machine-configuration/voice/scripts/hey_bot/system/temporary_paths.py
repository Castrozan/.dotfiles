from __future__ import annotations

import os
import tempfile
from pathlib import Path


def temporary_directory() -> Path:
    return Path(tempfile.gettempdir())


def create_temporary_file(prefix: str, suffix: str) -> Path:
    file_descriptor, created_path = tempfile.mkstemp(prefix=prefix, suffix=suffix)
    os.close(file_descriptor)
    return Path(created_path)
