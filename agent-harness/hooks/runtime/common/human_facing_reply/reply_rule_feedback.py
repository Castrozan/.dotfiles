#!/usr/bin/env python3

from __future__ import annotations


REPLY_RECOVERY_INSTRUCTION = (
    "Load the humanize skill, then rewrite it using that policy and the interactive "
    "communication instructions. Keep the answer and remove only filler."
)


def bounce_guidance(violations: list[str]) -> str:
    return (
        "Reply breaks the enforced interactive rules ("
        + "; ".join(violations)
        + "). "
        + REPLY_RECOVERY_INSTRUCTION
    )
