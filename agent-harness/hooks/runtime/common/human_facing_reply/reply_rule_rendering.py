#!/usr/bin/env python3

from __future__ import annotations

import textwrap

from reply_rule_catalog import rules_applying_to, rules_in_tier
from reply_template_limits import (
    ALWAYS_ENFORCED_TIER,
    EVERY_HUMAN_FACING_CHANNEL_SCOPE,
    INSTRUCTION_SURFACE_WRAP_COLUMN,
    REQUEST_GATED_TIER,
)

GENERATED_SURFACE_NOTICE = (
    "This file is generated from the reply rule catalog in `agent-harness/hooks/runtime/common/human_facing_reply`, the one place "
    "these rules exist as prose, as regex, and as the reminder the hooks inject. Edit that catalog and run "
    "`agent-harness/agent-instructions/core-rules/communication/render-enforced-reply-rules-markdown.py` rather than editing this file, which CI checks "
    "character for character against the catalog."
)

REPLY_TEMPLATE_SHAPE = (
    "Every reply is a short plain-prose status report. Open with a header-less paragraph that answers directly and "
    "gives the cause or the context, so it stands alone if the user stops reading there. Follow it with a `**Done:**` "
    "line saying what changed or what you found this turn, then a `**Next:**` line saying what is pending or the "
    "single decision you need from him, or `**Next:** nothing pending` when the task is finished. Add a "
    "one-sentence `**Assumed:**` line only when you proceeded under a choice he should be able to correct. A one or "
    "two sentence confirmation may be the opening paragraph alone."
)

REPLY_RECOVERY_INSTRUCTION = (
    "Rewrite the reply so it satisfies the rules it broke, keeping the substance the user needs and cutting only "
    "filler, never the answer."
)

REQUEST_GATE_CONDITION = (
    "These stand down only when the user explicitly asked for a document or an in-detail write-up, and fenced code "
    "blocks never count toward the line, word, and character counts."
)


def joined_rule_sentences(enforcement_tier: str) -> str:
    return " ".join(
        rule.instruction_sentence for rule in rules_in_tier(enforcement_tier)
    )


def joined_scope_sentences(channel_scope: str) -> str:
    return " ".join(
        rule.instruction_sentence for rule in rules_applying_to(channel_scope)
    )


def rendered_reply_reminder() -> str:
    return " ".join(
        (
            REPLY_TEMPLATE_SHAPE,
            joined_rule_sentences(ALWAYS_ENFORCED_TIER),
            joined_rule_sentences(REQUEST_GATED_TIER),
            REQUEST_GATE_CONDITION,
        )
    )


def rendered_bounce_guidance(violations: list[str]) -> str:
    return (
        "End-of-turn reply breaks the enforced plain-prose template ("
        + "; ".join(violations)
        + "). "
        + REPLY_RECOVERY_INSTRUCTION
        + " "
        + REPLY_TEMPLATE_SHAPE
    )


def wrapped_instruction_paragraph(paragraph: str) -> str:
    return textwrap.fill(
        paragraph,
        width=INSTRUCTION_SURFACE_WRAP_COLUMN,
        break_long_words=False,
        break_on_hyphens=False,
    )


def rendered_markdown_surface(sections) -> str:
    return (
        "\n\n".join(
            f"<{tag}>\n{wrapped_instruction_paragraph(body)}\n</{tag}>"
            for tag, body in sections
        )
        + "\n"
    )


def rendered_every_channel_wording_rules_markdown() -> str:
    return rendered_markdown_surface(
        (
            ("generated_surface", GENERATED_SURFACE_NOTICE),
            (
                "binds_every_human_facing_channel",
                "These rules hold for every text a human reads, a chat reply, a commit message, a merge request "
                "body, a ticket comment, a report, a published page, not only for the live keyboard reply where a "
                "hook checks them. "
                + joined_scope_sentences(EVERY_HUMAN_FACING_CHANNEL_SCOPE),
            ),
        )
    )


def rendered_enforced_reply_rules_markdown() -> str:
    sections = (
        ("generated_surface", GENERATED_SURFACE_NOTICE),
        ("reply_template", REPLY_TEMPLATE_SHAPE),
        (
            "always_enforced",
            "The Stop hook blocks the turn on any of these, including on a turn where the user asked for a document. "
            + joined_rule_sentences(ALWAYS_ENFORCED_TIER),
        ),
        (
            "request_gated",
            "The Stop hook blocks the turn on these too. "
            + REQUEST_GATE_CONDITION
            + " "
            + joined_rule_sentences(REQUEST_GATED_TIER),
        ),
    )
    return rendered_markdown_surface(sections)
