#!/usr/bin/env python3

from __future__ import annotations

from reply_format_configuration import REPLY_FORMAT_CONFIGURATION
from reply_rule_violations import (
    duplicate_label_violation,
    label_inline_content_violation,
    label_order_violation,
    labeled_section_ceiling_violation,
    list_block_length_violation,
    list_line_word_violation,
    missing_required_labels_violation,
    narration_opener_violation,
    per_label_ceiling_violation,
    reaction_opener_violation,
    sentence_dash_violation,
    unemphasized_label_violation,
    unlabeled_body_ceiling_violation,
    unlinked_artifact_violation,
    unseparated_label_violation,
)
from reply_text_metrics import ReplyUnderReview


REPLY_RESTRICTION_VALIDATORS = {
    "unlinked_artifact": unlinked_artifact_violation,
    "required_labels": missing_required_labels_violation,
    "label_emphasis": unemphasized_label_violation,
    "label_separation": unseparated_label_violation,
    "label_inline_content": label_inline_content_violation,
    "label_order": label_order_violation,
    "duplicate_label": duplicate_label_violation,
    "labeled_section_ceiling": labeled_section_ceiling_violation,
    "per_label_ceiling": per_label_ceiling_violation,
    "unlabeled_body_ceiling": unlabeled_body_ceiling_violation,
    "list_block_length": list_block_length_violation,
    "list_line_words": list_line_word_violation,
    "sentence_dash": sentence_dash_violation,
    "reaction_opener": reaction_opener_violation,
    "narration_opener": narration_opener_violation,
}


def violations_from_rules(reply: ReplyUnderReview) -> list[str]:
    return [
        violation
        for violation in (
            REPLY_RESTRICTION_VALIDATORS[name](reply)
            for name in reply.configuration.restrictions
        )
        if violation
    ]


def template_violations_in_reply(
    reply_text: str,
    *,
    configuration=REPLY_FORMAT_CONFIGURATION,
) -> list[str]:
    return violations_from_rules(ReplyUnderReview(reply_text, configuration))
