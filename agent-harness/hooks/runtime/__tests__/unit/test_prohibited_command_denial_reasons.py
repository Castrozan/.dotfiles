"""A denial says what is blocked and where to read the rest.

A reason is pasted into the agent's context every time the guard fires, so a
recipe inlined there is paid for on every repeat offence and competes with the
work in view. The detail belongs where it is already maintained: a reference
file beside the hook, or the skill that owns the tool.
"""

import sys
from pathlib import Path

import pytest

HOOKS_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(HOOKS_ROOT / "pre-tool-use" / "prohibited-command-guard"))

from prohibited_command_patterns import (  # noqa: E402
    PROHIBITED_PATTERNS_BY_TOOL,
)

DENIAL_REASON_CHARACTER_CEILING = 260


def every_denial_reason():
    seen_reasons = []
    for rules in PROHIBITED_PATTERNS_BY_TOOL.values():
        for rule in rules:
            if rule[1] not in seen_reasons:
                seen_reasons.append(rule[1])
    return seen_reasons


@pytest.mark.parametrize("reason", every_denial_reason())
def test_a_denial_reason_stays_short_enough_to_read_at_a_glance(reason):
    assert len(reason) <= DENIAL_REASON_CHARACTER_CEILING, (
        "point at the file or skill that owns the detail instead of reciting it; "
        f"this reason is {len(reason)} characters: {reason}"
    )


@pytest.mark.parametrize("reason", every_denial_reason())
def test_a_denial_reason_names_the_way_forward(reason):
    assert reason.rstrip().endswith("."), (
        "a denial ends as a complete instruction, not a trailing fragment"
    )
