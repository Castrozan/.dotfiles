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


def mechanical_repair_guidance(violations: list[str], repaired_reply: str) -> str:
    return (
        "Reply breaks the enforced interactive rules ("
        + "; ".join(violations)
        + "). Every violation is mechanical, so no rewrite is needed: send the "
        "corrected reply below verbatim as your whole answer.\n\n" + repaired_reply
    )
