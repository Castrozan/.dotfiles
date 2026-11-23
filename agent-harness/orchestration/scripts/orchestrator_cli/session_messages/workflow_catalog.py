from __future__ import annotations

import json
import os
from pathlib import Path

CATALOG_FILE = "dotfiles/workflow-commands.json"


def workflow_catalog_path() -> Path:
    data_home = Path(os.environ.get("XDG_DATA_HOME") or "~/.local/share").expanduser()
    return data_home / CATALOG_FILE


def installed_workflow_purposes() -> dict[str, str]:
    try:
        entries = json.loads(workflow_catalog_path().read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}
    return {entry["command"]: entry["purpose"] for entry in entries}
