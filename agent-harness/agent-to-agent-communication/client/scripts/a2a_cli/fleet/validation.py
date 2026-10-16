"""Validation shared by registry input boundaries."""

import math
import re


def label(value, field):
    if not isinstance(value, str):
        raise ValueError(f"{field} must be a nonempty string of at most 512 characters")
    if not value.strip() or len(value) > 512:
        raise ValueError(f"{field} must be a nonempty string of at most 512 characters")
    if contains_control_character(value):
        raise ValueError(f"{field} must not contain control characters")
    return value


def validate_timestamp(observed_at, now):
    if not isinstance(observed_at, (int, float)):
        raise ValueError("invalid or future evidence timestamp")
    if not math.isfinite(observed_at):
        raise ValueError("invalid or future evidence timestamp")
    if observed_at < 0 or observed_at > now + 5:
        raise ValueError("invalid or future evidence timestamp")


def validate_transport(transport):
    if transport == "local":
        return
    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_.-]{0,127}", transport):
        raise ValueError("transport must be local or an existing SSH alias")


def contains_control_character(value):
    return any(ord(character) < 32 for character in value)
