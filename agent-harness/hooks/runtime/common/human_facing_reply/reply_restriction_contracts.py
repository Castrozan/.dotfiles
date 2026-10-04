from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import TYPE_CHECKING

from reply_link_format import formatted_link_violation
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
    table_indexes_violation,
    unemphasized_label_violation,
    unlabeled_body_ceiling_violation,
    unlinked_artifact_violation,
    unseparated_label_violation,
)

if TYPE_CHECKING:
    from reply_text_metrics import ReplyUnderReview


@dataclass(frozen=True)
class ReplyRestriction:
    evaluate: Callable[[ReplyUnderReview], str | None]
    parameters: frozenset[str] = frozenset()
    placeholders: frozenset[str] = frozenset()


REPLY_RESTRICTIONS = {
    "unlinked_artifact": ReplyRestriction(
        unlinked_artifact_violation,
        frozenset({"pattern", "required_pattern", "url_pattern", "kind_paths"}),
    ),
    "required_labels": ReplyRestriction(
        missing_required_labels_violation,
        placeholders=frozenset({"word_count", "maximum_words", "missing_labels"}),
    ),
    "formatted_link": ReplyRestriction(formatted_link_violation),
    "label_emphasis": ReplyRestriction(
        unemphasized_label_violation, placeholders=frozenset({"label"})
    ),
    "label_separation": ReplyRestriction(
        unseparated_label_violation, placeholders=frozenset({"label"})
    ),
    "label_inline_content": ReplyRestriction(
        label_inline_content_violation, placeholders=frozenset({"label"})
    ),
    "label_order": ReplyRestriction(
        label_order_violation, placeholders=frozenset({"expected_labels"})
    ),
    "duplicate_label": ReplyRestriction(
        duplicate_label_violation, placeholders=frozenset({"label"})
    ),
    "labeled_section_ceiling": ReplyRestriction(
        labeled_section_ceiling_violation,
        placeholders=frozenset({"word_count", "maximum_words", "grace_words"}),
    ),
    "per_label_ceiling": ReplyRestriction(
        per_label_ceiling_violation,
        placeholders=frozenset({"word_count", "maximum_words", "grace_words", "label"}),
    ),
    "unlabeled_body_ceiling": ReplyRestriction(
        unlabeled_body_ceiling_violation,
        placeholders=frozenset({"word_count", "maximum_words", "grace_words"}),
    ),
    "list_block_length": ReplyRestriction(
        list_block_length_violation,
        placeholders=frozenset({"line_count", "maximum_lines"}),
    ),
    "list_line_words": ReplyRestriction(
        list_line_word_violation,
        placeholders=frozenset({"word_count", "maximum_words", "grace_words"}),
    ),
    "table_indexes": ReplyRestriction(
        table_indexes_violation, placeholders=frozenset({"table_number"})
    ),
    "sentence_dash": ReplyRestriction(
        sentence_dash_violation,
        frozenset({"characters"}),
        frozenset({"character_name"}),
    ),
    "reaction_opener": ReplyRestriction(
        reaction_opener_violation, frozenset({"pattern"})
    ),
    "narration_opener": ReplyRestriction(
        narration_opener_violation, frozenset({"pattern"})
    ),
}
