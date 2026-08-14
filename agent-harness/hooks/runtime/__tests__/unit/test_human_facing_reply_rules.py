import re
import sys
from pathlib import Path

HOOKS_ROOT = Path(__file__).resolve().parents[2]
REPLY_RULE_MODULE_DIRECTORY = next(HOOKS_ROOT.rglob("reply_rule_catalog.py")).parent
if str(REPLY_RULE_MODULE_DIRECTORY) not in sys.path:
    sys.path.insert(0, str(REPLY_RULE_MODULE_DIRECTORY))

from long_form_request_gate import user_request_permits_long_form  # noqa: E402
from reply_rule_catalog import template_violations_in_reply  # noqa: E402
from reply_rule_feedback import bounce_guidance  # noqa: E402
from reply_template_limits import (  # noqa: E402
    MAXIMUM_PROSE_PARAGRAPH_BLOCKS,
    REPLY_HARD_CHARACTER_CEILING,
    REPLY_HARD_WORD_CEILING,
    REPLY_TARGET_PROSE_WORDS,
    SCANNABLE_MAXIMUM_PROSE_LINES,
    SHORT_CONFIRMATION_MAXIMUM_PROSE_LINES,
)

INTERACTIVE_COMMUNICATION_PATH = (
    REPLY_RULE_MODULE_DIRECTORY / "interactive-communication.md"
)


def test_long_form_granted_for_explicit_document_request():
    assert user_request_permits_long_form(
        "write me a design doc for the reports service"
    )
    assert user_request_permits_long_form("create a design doc for the reports service")
    assert user_request_permits_long_form("make me a runbook for the deploy")
    assert user_request_permits_long_form("write the documentation for the API")
    assert user_request_permits_long_form("give me a full architecture overview")
    assert user_request_permits_long_form("explain in detail why the sync failed")
    assert user_request_permits_long_form("paste the entire file verbatim")
    assert user_request_permits_long_form("give me the design of the hook stuff")
    assert user_request_permits_long_form("what is the architecture behind the gate")


def test_long_form_not_granted_for_routine_requests():
    assert not user_request_permits_long_form("is obsidian syncing on chise?")
    assert not user_request_permits_long_form("fix the rebuild and commit it")
    assert not user_request_permits_long_form("show me the diff")
    assert not user_request_permits_long_form("")


def test_long_form_not_granted_for_verb_substring_or_compression_leaks():
    assert not user_request_permits_long_form("what's the sprint plan?")
    assert not user_request_permits_long_form("fix the footprint report")
    assert not user_request_permits_long_form(
        "can you reproduce the deploy plan failure"
    )
    assert not user_request_permits_long_form("give me a quick summary of what changed")
    assert not user_request_permits_long_form("show me the deploy report")
    assert not user_request_permits_long_form(
        "why did you show me that? update the deploy plan status"
    )
    assert not user_request_permits_long_form("when is the design review meeting?")


def test_routine_long_reply_trips_the_hard_ceiling():
    reply = " ".join(["word"] * (REPLY_HARD_WORD_CEILING + 10))
    violations = template_violations_in_reply(reply, "is obsidian syncing?")
    assert any("hard ceiling" in v for v in violations)


def test_routine_char_heavy_reply_trips_the_character_ceiling():
    reply = "x" * (REPLY_HARD_CHARACTER_CEILING + 50)
    violations = template_violations_in_reply(reply, "is obsidian syncing?")
    assert any("character hard ceiling" in v for v in violations)
    assert not any("word hard ceiling" in v for v in violations)


def test_long_form_request_skips_length_and_shape_but_keeps_hygiene():
    long_reply_with_header = "## Overview\n" + " ".join(
        ["word"] * (REPLY_HARD_WORD_CEILING + 50)
    )
    violations = template_violations_in_reply(
        long_reply_with_header, "write a design doc"
    )
    assert violations == []

    violations_with_em_dash = template_violations_in_reply(
        long_reply_with_header + " — tail", "write a design doc"
    )
    assert violations_with_em_dash == ["contains an em dash"]


def test_deferring_to_an_earlier_message_is_flagged_even_under_long_form():
    defer_message = "defers to an earlier message instead of standing alone"

    routine = template_violations_in_reply(
        "As I said above, the rebuild is green.", "is obsidian syncing?"
    )
    assert defer_message in routine

    long_form = template_violations_in_reply(
        "## Overview\nSee my prior message for the full breakdown.",
        "write a design doc",
    )
    assert long_form == [defer_message]


def test_an_en_dash_is_caught_like_an_em_dash():
    violations = template_violations_in_reply(
        "The rebuild is green – CI agrees.", "write a design doc"
    )
    assert violations == ["contains an en dash"]


def test_a_dash_inside_a_fenced_block_is_a_quoted_artifact_not_prose():
    reply = "The upstream README reads:\n```\nrange 1–9 — inclusive\n```\nNothing else."
    assert template_violations_in_reply(reply, "write a design doc") == []


def test_bounce_guidance_names_the_violation_and_points_to_loaded_policy():
    guidance = bounce_guidance(["contains an em dash"])

    assert "contains an em dash" in guidance
    assert "loaded humanize skill" in guidance
    assert "interactive communication instructions" in guidance


def test_interactive_instructions_state_the_hook_limit_values():
    policy = re.sub(
        r"\s+",
        " ",
        INTERACTIVE_COMMUNICATION_PATH.read_text(encoding="utf-8"),
    )

    expected_limits = (
        f"longer than {SHORT_CONFIRMATION_MAXIMUM_PROSE_LINES} prose lines",
        f"within {SCANNABLE_MAXIMUM_PROSE_LINES} prose lines",
        f"about {REPLY_TARGET_PROSE_WORDS} prose words",
        f"never exceed {REPLY_HARD_WORD_CEILING}",
        f"within {REPLY_HARD_CHARACTER_CEILING} prose characters",
        f"no more than {MAXIMUM_PROSE_PARAGRAPH_BLOCKS} prose blocks",
    )
    assert not [limit for limit in expected_limits if limit not in policy]
