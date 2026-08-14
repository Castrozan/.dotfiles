#!/usr/bin/env python3

from __future__ import annotations


REPLY_RECOVERY_INSTRUCTION = (
    "Rewrite it using the injected humanize policy and interactive communication "
    "instructions. Keep the answer and remove only filler."
)


def bounce_guidance(violations: list[str]) -> str:
    return (
        "Reply breaks the enforced interactive rules ("
        + "; ".join(violations)
        + "). "
        + REPLY_RECOVERY_INSTRUCTION
    )
