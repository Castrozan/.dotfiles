#!/usr/bin/env python3

from __future__ import annotations

from long_form_request_gate import user_request_permits_long_form
from reply_rule_violations import (
    bullet_or_numbered_list_violation,
    character_ceiling_violation,
    earlier_message_deferral_violation,
    missing_done_and_next_labels_violation,
    narration_opener_violation,
    paragraph_block_ceiling_violation,
    reaction_opener_violation,
    scannable_line_ceiling_violation,
    section_header_violation,
    sentence_dash_violation,
    unlinked_artifact_violation,
    word_ceiling_violation,
)
from reply_template_limits import (
    ALWAYS_ENFORCED_TIER,
    EVERY_HUMAN_FACING_CHANNEL_SCOPE,
    LIVE_KEYBOARD_REPLY_SCOPE,
    MAXIMUM_PROSE_PARAGRAPH_BLOCKS,
    REPLY_HARD_CHARACTER_CEILING,
    REPLY_HARD_WORD_CEILING,
    REPLY_TARGET_PROSE_WORDS,
    REQUEST_GATED_TIER,
    SCANNABLE_MAXIMUM_PROSE_LINES,
    SHORT_CONFIRMATION_MAXIMUM_PROSE_LINES,
)
from reply_text_metrics import ReplyUnderReview


class HumanFacingReplyRule:
    def __init__(
        self,
        name: str,
        enforcement_tier: str,
        applies_to: str,
        instruction_sentence: str,
        violation_of,
    ):
        self.name = name
        self.enforcement_tier = enforcement_tier
        self.applies_to = applies_to
        self.instruction_sentence = instruction_sentence
        self.violation_of = violation_of


HUMAN_FACING_REPLY_RULES = [
    HumanFacingReplyRule(
        "sentence_dash",
        ALWAYS_ENFORCED_TIER,
        EVERY_HUMAN_FACING_CHANNEL_SCOPE,
        "Never use an em dash or an en dash in prose; recast with a comma, a colon, or two sentences.",
        sentence_dash_violation,
    ),
    HumanFacingReplyRule(
        "reaction_opener",
        ALWAYS_ENFORCED_TIER,
        EVERY_HUMAN_FACING_CHANNEL_SCOPE,
        'Never open with a reaction or a sycophancy phrase ("You are right", "Good catch", "Sure", "Of course").',
        reaction_opener_violation,
    ),
    HumanFacingReplyRule(
        "narration_opener",
        ALWAYS_ENFORCED_TIER,
        EVERY_HUMAN_FACING_CHANNEL_SCOPE,
        'Never open by narrating what you are about to do ("Let me", "I will go ahead").',
        narration_opener_violation,
    ),
    HumanFacingReplyRule(
        "earlier_message_deferral",
        ALWAYS_ENFORCED_TIER,
        LIVE_KEYBOARD_REPLY_SCOPE,
        "Never point back to an earlier message or turn, because Lucas reads only this end-of-turn message; "
        "restate what still matters so the reply stands alone.",
        earlier_message_deferral_violation,
    ),
    HumanFacingReplyRule(
        "unlinked_artifact",
        ALWAYS_ENFORCED_TIER,
        EVERY_HUMAN_FACING_CHANNEL_SCOPE,
        "Give the link for any merge request or pull request you name, so Lucas clicks through to validate it.",
        unlinked_artifact_violation,
    ),
    HumanFacingReplyRule(
        "prose_over_lists",
        REQUEST_GATED_TIER,
        LIVE_KEYBOARD_REPLY_SCOPE,
        "Carry every point in prose sentences, with no bullet lists and no numbered lists.",
        bullet_or_numbered_list_violation,
    ),
    HumanFacingReplyRule(
        "no_section_headers",
        REQUEST_GATED_TIER,
        LIVE_KEYBOARD_REPLY_SCOPE,
        "Use no section headers beyond the Done, Next, and Assumed labels.",
        section_header_violation,
    ),
    HumanFacingReplyRule(
        "done_and_next_labels",
        REQUEST_GATED_TIER,
        LIVE_KEYBOARD_REPLY_SCOPE,
        f"Any reply longer than {SHORT_CONFIRMATION_MAXIMUM_PROSE_LINES} prose lines carries both the Done label "
        "and the Next label.",
        missing_done_and_next_labels_violation,
    ),
    HumanFacingReplyRule(
        "scannable_line_ceiling",
        REQUEST_GATED_TIER,
        LIVE_KEYBOARD_REPLY_SCOPE,
        f"Keep the reply inside {SCANNABLE_MAXIMUM_PROSE_LINES} prose lines.",
        scannable_line_ceiling_violation,
    ),
    HumanFacingReplyRule(
        "word_ceiling",
        REQUEST_GATED_TIER,
        LIVE_KEYBOARD_REPLY_SCOPE,
        f"Aim for roughly {REPLY_TARGET_PROSE_WORDS} prose words and never pass {REPLY_HARD_WORD_CEILING}; a turn "
        "carrying real substance may run past the target, so cut filler rather than the answer.",
        word_ceiling_violation,
    ),
    HumanFacingReplyRule(
        "character_ceiling",
        REQUEST_GATED_TIER,
        LIVE_KEYBOARD_REPLY_SCOPE,
        f"Keep the reply inside {REPLY_HARD_CHARACTER_CEILING} prose characters.",
        character_ceiling_violation,
    ),
    HumanFacingReplyRule(
        "paragraph_block_ceiling",
        REQUEST_GATED_TIER,
        LIVE_KEYBOARD_REPLY_SCOPE,
        f"Stack no more than {MAXIMUM_PROSE_PARAGRAPH_BLOCKS} prose blocks: the opening paragraph, Done, Next, and "
        "an optional Assumed line.",
        paragraph_block_ceiling_violation,
    ),
]


def rules_applying_to(channel_scope: str) -> list[HumanFacingReplyRule]:
    return [
        rule for rule in HUMAN_FACING_REPLY_RULES if rule.applies_to == channel_scope
    ]


def rules_in_tier(enforcement_tier: str) -> list[HumanFacingReplyRule]:
    return [
        rule
        for rule in HUMAN_FACING_REPLY_RULES
        if rule.enforcement_tier == enforcement_tier
    ]


def violations_from_rules(
    reply: ReplyUnderReview, rules: list[HumanFacingReplyRule]
) -> list[str]:
    return [
        violation
        for violation in (rule.violation_of(reply) for rule in rules)
        if violation
    ]


def template_violations_in_reply(
    reply_text: str, user_request_text: str = ""
) -> list[str]:
    applicable_rules = rules_in_tier(ALWAYS_ENFORCED_TIER)
    if not user_request_permits_long_form(user_request_text):
        applicable_rules = applicable_rules + rules_in_tier(REQUEST_GATED_TIER)
    return violations_from_rules(ReplyUnderReview(reply_text), applicable_rules)
