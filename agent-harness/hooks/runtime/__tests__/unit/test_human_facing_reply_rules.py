import sys
from pathlib import Path

HOOKS_ROOT = Path(__file__).resolve().parents[2]
REPLY_RULE_MODULE_DIRECTORY = next(HOOKS_ROOT.rglob("reply_rule_catalog.py")).parent
if str(REPLY_RULE_MODULE_DIRECTORY) not in sys.path:
    sys.path.insert(0, str(REPLY_RULE_MODULE_DIRECTORY))

from long_form_request_gate import user_request_permits_long_form  # noqa: E402
from reply_rule_catalog import (  # noqa: E402
    HUMAN_FACING_REPLY_RULES,
    template_violations_in_reply,
)
from reply_rule_rendering import (  # noqa: E402
    rendered_bounce_guidance,
    rendered_enforced_reply_rules_markdown,
    rendered_every_channel_wording_rules_markdown,
)
from reply_template_limits import (  # noqa: E402
    EVERY_HUMAN_FACING_CHANNEL_SCOPE,
    LIVE_KEYBOARD_REPLY_SCOPE,
    REPLY_HARD_CHARACTER_CEILING,
    REPLY_HARD_WORD_CEILING,
)

REPOSITORY_ROOT = HOOKS_ROOT.parents[2]
GENERATED_SURFACES = (
    (
        REPOSITORY_ROOT
        / "agent-harness"
        / "agent-instructions"
        / "core-rules"
        / "communication"
        / "enforced-reply-rules.md",
        rendered_enforced_reply_rules_markdown,
    ),
    (
        REPOSITORY_ROOT
        / "agent-harness"
        / "agent-instructions"
        / "skills"
        / "humanize"
        / "enforced-wording-rules.md",
        rendered_every_channel_wording_rules_markdown,
    ),
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


def test_every_rule_carries_an_instruction_sentence_for_the_rendered_surfaces():
    without_sentence = [
        rule.name
        for rule in HUMAN_FACING_REPLY_RULES
        if not rule.instruction_sentence.strip()
    ]
    assert not without_sentence, (
        "a rule enforced by regex but never stated to the model is the drift this "
        f"catalog exists to prevent: {without_sentence}"
    )


def test_the_bounce_text_carries_the_violations_and_the_template():
    bounce = rendered_bounce_guidance(["contains an em dash"])
    assert "contains an em dash" in bounce
    assert "**Done:**" in bounce


def test_every_committed_generated_surface_matches_the_catalog():
    stale = [
        str(surface_path.relative_to(REPOSITORY_ROOT))
        for surface_path, render in GENERATED_SURFACES
        if surface_path.read_text(encoding="utf-8") != render()
    ]
    assert not stale, (
        "these surfaces are generated; run "
        "agent-harness/agent-instructions/core-rules/communication/render-enforced-reply-rules-markdown.py after editing the rule "
        f"catalog so the deployed instruction text matches what the hook enforces: {stale}"
    )


def test_every_rule_declares_the_channels_it_binds():
    known_scopes = {EVERY_HUMAN_FACING_CHANNEL_SCOPE, LIVE_KEYBOARD_REPLY_SCOPE}
    unscoped = [
        rule.name
        for rule in HUMAN_FACING_REPLY_RULES
        if rule.applies_to not in known_scopes
    ]
    assert not unscoped, (
        "a rule with no channel scope reaches neither the humanize chapter nor the "
        f"reply surface, so it would be enforced without ever being stated: {unscoped}"
    )
