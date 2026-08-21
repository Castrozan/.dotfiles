#!/usr/bin/env python3

from __future__ import annotations

from reply_rule_violations import (
    labeled_section_ceiling_violation,
    list_block_length_violation,
    list_line_word_violation,
    missing_required_labels_violation,
    narration_opener_violation,
    reaction_opener_violation,
    sentence_dash_violation,
    unemphasized_label_violation,
    unlinked_artifact_violation,
    unseparated_label_violation,
    word_ceiling_violation,
)
from reply_text_metrics import ReplyUnderReview


class HumanFacingReplyRule:
    def __init__(self, name: str, violation_of):
        self.name = name
        self.violation_of = violation_of


HUMAN_FACING_REPLY_RULES = [
    HumanFacingReplyRule("unlinked_artifact", unlinked_artifact_violation),
    HumanFacingReplyRule("required_labels", missing_required_labels_violation),
    HumanFacingReplyRule("label_emphasis", unemphasized_label_violation),
    HumanFacingReplyRule("label_separation", unseparated_label_violation),
    HumanFacingReplyRule("labeled_section_ceiling", labeled_section_ceiling_violation),
    HumanFacingReplyRule("word_ceiling", word_ceiling_violation),
    HumanFacingReplyRule("list_block_length", list_block_length_violation),
    HumanFacingReplyRule("list_line_words", list_line_word_violation),
    HumanFacingReplyRule("sentence_dash", sentence_dash_violation),
    HumanFacingReplyRule("reaction_opener", reaction_opener_violation),
    HumanFacingReplyRule("narration_opener", narration_opener_violation),
]


def violations_from_rules(reply: ReplyUnderReview) -> list[str]:
    return [
        violation
        for violation in (rule.violation_of(reply) for rule in HUMAN_FACING_REPLY_RULES)
        if violation
    ]


def template_violations_in_reply(
    reply_text: str, user_request_text: str = ""
) -> list[str]:
    return violations_from_rules(ReplyUnderReview(reply_text))
