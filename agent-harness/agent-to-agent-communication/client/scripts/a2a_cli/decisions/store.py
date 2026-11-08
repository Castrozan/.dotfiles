from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path

from .cards import InvalidDecisionCard


def default_decision_directory() -> Path:
    state_home = Path(os.environ.get("XDG_STATE_HOME", "~/.local/state")).expanduser()
    return state_home / "a2a-decisions"


def card_path(directory: Path, identifier: str) -> Path:
    if not identifier or "/" in identifier or identifier.startswith("."):
        raise InvalidDecisionCard(f"{identifier!r} is not a decision id")
    return directory / f"{identifier}.json"


def save_card(directory: Path, card: dict) -> Path:
    directory.mkdir(parents=True, exist_ok=True)
    destination = card_path(directory, card["id"])
    file_descriptor, temporary_name = tempfile.mkstemp(dir=directory, suffix=".tmp")
    with os.fdopen(file_descriptor, "w", encoding="utf-8") as temporary_file:
        json.dump(card, temporary_file, indent=2, ensure_ascii=False)
    os.replace(temporary_name, destination)
    return destination


def load_card(directory: Path, identifier: str) -> dict:
    path = card_path(directory, identifier)
    if not path.is_file():
        raise InvalidDecisionCard(f"no decision {identifier} in {directory}")
    return json.loads(path.read_text(encoding="utf-8"))


def all_cards(directory: Path) -> list[dict]:
    if not directory.is_dir():
        return []
    return sorted(
        (
            json.loads(path.read_text(encoding="utf-8"))
            for path in directory.glob("D-*.json")
        ),
        key=lambda card: card["created_at"],
    )
