from __future__ import annotations

from datetime import datetime, timezone


class InvalidPeerDocument(Exception):
    pass


def current_timestamp() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def is_nonempty_text(value) -> bool:
    return isinstance(value, str) and bool(value.strip())


def nonempty_text(document: dict, field: str) -> str:
    value = document.get(field)
    if not is_nonempty_text(value):
        raise InvalidPeerDocument(f"{field} must be nonempty text")
    return value.strip()


def text_items(value, field: str) -> list[str]:
    if not isinstance(value, list) or not all(map(is_nonempty_text, value)):
        raise InvalidPeerDocument(f"{field} must be a list of nonempty text")
    return [item.strip() for item in value]


def required_text_items(document: dict, field: str) -> list[str]:
    items = text_items(document.get(field), field)
    if not items:
        raise InvalidPeerDocument(f"{field} must list at least one item")
    return items


def optional_text_items(document: dict, field: str) -> list[str]:
    return text_items(document.get(field, []), field)


def require_object(document, description: str) -> dict:
    if not isinstance(document, dict):
        raise InvalidPeerDocument(f"{description} must be a JSON object")
    return document
