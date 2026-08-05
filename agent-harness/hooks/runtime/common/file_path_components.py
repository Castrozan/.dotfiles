from __future__ import annotations

import os

PATH_SEPARATORS = {"/", os.sep}


def path_components(file_path: str) -> list[str]:
    normalized = file_path
    for separator in PATH_SEPARATORS:
        normalized = normalized.replace(separator, "/")
    return [component for component in normalized.split("/") if component]
