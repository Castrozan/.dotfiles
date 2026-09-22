from reply_artifact_links import reply_has_unlinked_artifacts
from reply_format_configuration import exceeds_word_budget
from reply_text_metrics import ReplyUnderReview


def sentence_dash_violation(reply: ReplyUnderReview) -> str | None:
    configuration = reply.configuration
    for character, character_name in configuration.restrictions["sentence_dash"][
        "characters"
    ].items():
        if character in reply.prose_without_quotations:
            return configuration.violation(
                "sentence_dash", character_name=character_name
            )
    return None


def opener_violation(reply: ReplyUnderReview, restriction: str) -> str | None:
    configuration = reply.configuration
    if configuration.restriction_patterns[restriction]["pattern"].match(
        reply.opening_text
    ):
        return configuration.violation(restriction)
    return None


def reaction_opener_violation(reply: ReplyUnderReview) -> str | None:
    return opener_violation(reply, "reaction_opener")


def narration_opener_violation(reply: ReplyUnderReview) -> str | None:
    return opener_violation(reply, "narration_opener")


def unlinked_artifact_violation(reply: ReplyUnderReview) -> str | None:
    if reply_has_unlinked_artifacts(reply):
        return reply.configuration.violation("unlinked_artifact")
    return None


def missing_required_labels_violation(reply: ReplyUnderReview) -> str | None:
    if reply_is_a_short_confirmation(reply):
        return None
    configuration = reply.configuration
    missing_labels = [
        label for label in configuration.labels if label not in reply.labels_present
    ]
    if not missing_labels:
        return None
    return configuration.violation(
        "required_labels",
        word_count=reply.prose_word_count,
        maximum_words=configuration.formats["confirmation"]["maximum_words"],
        missing_labels="/".join(f"{label}:" for label in missing_labels),
    )


def labeled_section_ceiling_violation(reply: ReplyUnderReview) -> str | None:
    budget = reply.configuration.formats["labeled_reply"]["combined_labels"]
    if exceeds_word_budget(reply.labeled_section_word_count, budget):
        return reply.configuration.violation(
            "labeled_section_ceiling",
            word_count=reply.labeled_section_word_count,
            **budget,
        )
    return None


def unlabeled_body_ceiling_violation(reply: ReplyUnderReview) -> str | None:
    if reply_is_a_short_confirmation(reply):
        return None
    budget = reply.configuration.formats["labeled_reply"]["body"]
    if exceeds_word_budget(reply.unlabeled_body_word_count, budget):
        return reply.configuration.violation(
            "unlabeled_body_ceiling",
            word_count=reply.unlabeled_body_word_count,
            **budget,
        )
    return None


def per_label_ceiling_violation(reply: ReplyUnderReview) -> str | None:
    for label, budget in reply.configuration.labels.items():
        word_count = reply.per_label_word_counts.get(label)
        if word_count is not None and exceeds_word_budget(word_count, budget):
            return reply.configuration.violation(
                "per_label_ceiling", label=label, word_count=word_count, **budget
            )
    return None


def list_block_length_violation(reply: ReplyUnderReview) -> str | None:
    maximum_lines = reply.configuration.lists["maximum_lines"]
    for block in reply.list_blocks:
        if block.line_count > maximum_lines:
            return reply.configuration.violation(
                "list_block_length",
                line_count=block.line_count,
                maximum_lines=maximum_lines,
            )
    return None


def list_line_word_violation(reply: ReplyUnderReview) -> str | None:
    budget = reply.configuration.lists["item"]
    for block in reply.list_blocks:
        for item in block.items:
            word_count = item.word_count
            if exceeds_word_budget(word_count, budget):
                return reply.configuration.violation(
                    "list_line_words", word_count=word_count, **budget
                )
    return None


def reply_is_a_short_confirmation(reply: ReplyUnderReview) -> bool:
    return not exceeds_word_budget(
        reply.prose_word_count, reply.configuration.formats["confirmation"]
    )


def unemphasized_label_violation(reply: ReplyUnderReview) -> str | None:
    if reply_is_a_short_confirmation(reply):
        return None
    for label_line in reply.label_lines:
        if not label_line.is_emphasized:
            return reply.configuration.violation(
                "label_emphasis", label=label_line.label
            )
    return None


def unseparated_label_violation(reply: ReplyUnderReview) -> str | None:
    if reply_is_a_short_confirmation(reply):
        return None
    for label_line in reply.label_lines:
        if not label_line.preceded_by_blank_line:
            return reply.configuration.violation(
                "label_separation", label=label_line.label
            )
    return None


def duplicate_label_violation(reply: ReplyUnderReview) -> str | None:
    if reply_is_a_short_confirmation(reply):
        return None
    seen = set()
    for label in reply.label_lines:
        if label.label in seen:
            return reply.configuration.violation("duplicate_label", label=label.label)
        seen.add(label.label)
    return None


def label_order_violation(reply: ReplyUnderReview) -> str | None:
    if reply_is_a_short_confirmation(reply):
        return None
    expected = list(reply.configuration.labels)
    observed = list(dict.fromkeys(label.label for label in reply.label_lines))
    if observed != [label for label in expected if label in observed]:
        return reply.configuration.violation(
            "label_order", expected_labels=", ".join(expected)
        )
    return None
