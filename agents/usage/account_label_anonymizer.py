from __future__ import annotations

import hashlib
import json
from pathlib import Path

ACCOUNT_LABEL_NAMESPACE = "dotfiles-usage-account-v1"
MACHINE_LABEL_NAMESPACE = "dotfiles-usage-machine-v1"
OPAQUE_LABEL_LENGTH = 12


def derive_opaque_label(label_namespace: str, raw_identifier: str) -> str:
    namespaced_identifier = f"{label_namespace}:{raw_identifier}".encode("utf-8")
    return hashlib.sha256(namespaced_identifier).hexdigest()[:OPAQUE_LABEL_LENGTH]


def derive_account_label(account_uuid: str) -> str:
    return derive_opaque_label(ACCOUNT_LABEL_NAMESPACE, account_uuid)


def derive_machine_label(machine_hostname: str) -> str:
    return derive_opaque_label(MACHINE_LABEL_NAMESPACE, machine_hostname)


def default_claude_account_config_path() -> Path:
    return Path.home() / ".claude.json"


def read_current_account_uuid(claude_account_config_path: Path) -> str | None:
    if not claude_account_config_path.is_file():
        return None
    try:
        claude_account_config = json.loads(claude_account_config_path.read_text())
    except (json.JSONDecodeError, OSError):
        return None
    account_uuid = claude_account_config.get("oauthAccount", {}).get("accountUuid")
    return account_uuid or None
