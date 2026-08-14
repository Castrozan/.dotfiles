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
from reply_template_limits import ALWAYS_ENFORCED_TIER, REQUEST_GATED_TIER
from reply_text_metrics import ReplyUnderReview


class HumanFacingReplyRule:
    def __init__(self, name: str, enforcement_tier: str, violation_of):
        self.name = name
        self.enforcement_tier = enforcement_tier
        self.violation_of = violation_of


HUMAN_FACING_REPLY_RULES = [
    HumanFacingReplyRule(
        "sentence_dash",
        ALWAYS_ENFORCED_TIER,
        sentence_dash_violation,
    ),
    HumanFacingReplyRule(
        "reaction_opener",
        ALWAYS_ENFORCED_TIER,
        reaction_opener_violation,
    ),
    HumanFacingReplyRule(
        "narration_opener",
        ALWAYS_ENFORCED_TIER,
        narration_opener_violation,
    ),
    HumanFacingReplyRule(
        "earlier_message_deferral",
        ALWAYS_ENFORCED_TIER,
        earlier_message_deferral_violation,
    ),
    HumanFacingReplyRule(
        "unlinked_artifact",
        ALWAYS_ENFORCED_TIER,
        unlinked_artifact_violation,
    ),
    HumanFacingReplyRule(
        "prose_over_lists",
        REQUEST_GATED_TIER,
        bullet_or_numbered_list_violation,
    ),
    HumanFacingReplyRule(
        "no_section_headers",
        REQUEST_GATED_TIER,
        section_header_violation,
    ),
    HumanFacingReplyRule(
        "done_and_next_labels",
        REQUEST_GATED_TIER,
        missing_done_and_next_labels_violation,
    ),
    HumanFacingReplyRule(
        "scannable_line_ceiling",
        REQUEST_GATED_TIER,
        scannable_line_ceiling_violation,
    ),
    HumanFacingReplyRule(
        "word_ceiling",
        REQUEST_GATED_TIER,
        word_ceiling_violation,
    ),
    HumanFacingReplyRule(
        "character_ceiling",
        REQUEST_GATED_TIER,
        character_ceiling_violation,
    ),
    HumanFacingReplyRule(
        "paragraph_block_ceiling",
        REQUEST_GATED_TIER,
        paragraph_block_ceiling_violation,
    ),
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
