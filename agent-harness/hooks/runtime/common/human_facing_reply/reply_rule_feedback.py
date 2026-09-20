#!/usr/bin/env python3

from __future__ import annotations


REPLY_RECOVERY_INSTRUCTION = (
    "Repair exactly that in the reply you already wrote, against the response shape "
    "section of the interactive communication instructions you are already carrying. "
    "Keep the answer and remove only filler. Loading a skill is not needed, because "
    "every enforced rule is already stated in those instructions."
)


def bounce_guidance(violations: list[str]) -> str:
    return (
        "Reply breaks the enforced interactive rules ("
        + "; ".join(violations)
        + "). "
        + REPLY_RECOVERY_INSTRUCTION
    )
