REPLY_RESTRICTION_CONTRACTS = {
    "unlinked_artifact": (
        {"pattern", "required_pattern", "url_pattern", "kind_paths"},
        set(),
    ),
    "required_labels": (set(), {"word_count", "maximum_words", "missing_labels"}),
    "label_emphasis": (set(), {"label"}),
    "label_separation": (set(), {"label"}),
    "label_order": (set(), {"expected_labels"}),
    "duplicate_label": (set(), {"label"}),
    "labeled_section_ceiling": (
        set(),
        {"word_count", "maximum_words", "grace_words"},
    ),
    "per_label_ceiling": (
        set(),
        {"word_count", "maximum_words", "grace_words", "label"},
    ),
    "unlabeled_body_ceiling": (
        set(),
        {"word_count", "maximum_words", "grace_words"},
    ),
    "list_block_length": (set(), {"line_count", "maximum_lines"}),
    "list_line_words": (set(), {"word_count", "maximum_words", "grace_words"}),
    "sentence_dash": ({"characters"}, {"character_name"}),
    "reaction_opener": ({"pattern"}, set()),
    "narration_opener": ({"pattern"}, set()),
}
