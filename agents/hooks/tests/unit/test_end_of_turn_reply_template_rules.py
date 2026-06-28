import sys
from pathlib import Path

HOOKS_ROOT = Path(__file__).resolve().parents[2]
RULES_MODULE_DIRECTORY = next(
    HOOKS_ROOT.rglob("end_of_turn_reply_template_rules.py")
).parent
if str(RULES_MODULE_DIRECTORY) not in sys.path:
    sys.path.insert(0, str(RULES_MODULE_DIRECTORY))

from end_of_turn_reply_template_rules import (  # noqa: E402
    REPLY_HARD_WORD_CEILING,
    template_violations_in_reply,
    user_request_permits_long_form,
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


def test_routine_long_reply_trips_the_hard_ceiling():
    reply = " ".join(["word"] * (REPLY_HARD_WORD_CEILING + 10))
    violations = template_violations_in_reply(reply, "is obsidian syncing?")
    assert any("hard ceiling" in v for v in violations)


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
