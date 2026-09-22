#!/usr/bin/env python3

from __future__ import annotations

from itertools import groupby

from reply_format_configuration import REPLY_FORMAT_CONFIGURATION, exceeds_word_budget


def is_visual_line(line: str, configuration) -> bool:
    if line.strip().startswith(configuration.syntax["table_row_prefix"]):
        return True
    return any(
        character in configuration.syntax["box_drawing_characters"]
        for character in line
    )


def prose_lines_outside_visuals(reply_text: str, configuration) -> list[str]:
    prose_lines: list[str] = []
    inside_code_fence = False
    for line in reply_text.splitlines():
        if line.lstrip().startswith(configuration.syntax["code_fence_prefix"]):
            inside_code_fence = not inside_code_fence
            continue
        if inside_code_fence or not line.strip() or is_visual_line(line, configuration):
            continue
        prose_lines.append(line)
    return prose_lines


def list_line_blocks(prose_lines: list[str], configuration) -> list[list[str]]:
    blocks: list[list[str]] = []
    current_block: list[str] = []
    for line in prose_lines:
        if configuration.syntax_patterns["list_marker_pattern"].match(line):
            current_block.append(line)
            continue
        if current_block:
            blocks.append(current_block)
            current_block = []
    if current_block:
        blocks.append(current_block)
    return blocks


def prose_lines_outside_short_lists(prose_lines: list[str], configuration) -> list[str]:
    counted_lines: list[str] = []
    for is_list, grouped_lines in groupby(
        prose_lines,
        key=lambda line: bool(
            configuration.syntax_patterns["list_marker_pattern"].match(line)
        ),
    ):
        block = list(grouped_lines)
        if (
            is_list
            and len(block) <= configuration.lists["maximum_exempt_items"]
            and all(
                not exceeds_word_budget(len(line.split()), configuration.lists["item"])
                for line in block
            )
        ):
            continue
        counted_lines.extend(block)
    return counted_lines


def matched_reply_label(line: str, configuration) -> str | None:
    for label, pattern in configuration.label_patterns.items():
        if pattern.match(line):
            return label
    return None


class ReplyLabelLine:
    def __init__(
        self, label: str, text: str, preceded_by_blank_line: bool, configuration
    ):
        self.label = label
        self.text = text
        self.preceded_by_blank_line = preceded_by_blank_line
        self.is_emphasized = text.strip().startswith(
            configuration.syntax["label_emphasis_marker"]
        )


def reply_label_lines(reply_text: str, configuration) -> list[ReplyLabelLine]:
    label_lines: list[ReplyLabelLine] = []
    inside_code_fence = False
    previous_line_was_blank = True
    for line in reply_text.splitlines():
        if line.lstrip().startswith(configuration.syntax["code_fence_prefix"]):
            inside_code_fence = not inside_code_fence
            previous_line_was_blank = False
            continue
        if inside_code_fence:
            continue
        if not line.strip():
            previous_line_was_blank = True
            continue
        label = matched_reply_label(line, configuration)
        if label:
            label_lines.append(
                ReplyLabelLine(label, line, previous_line_was_blank, configuration)
            )
        previous_line_was_blank = False
    return label_lines


def labels_present_in(prose_lines: list[str], configuration) -> set[str]:
    return {
        label
        for label, pattern in configuration.label_patterns.items()
        if any(pattern.match(line) for line in prose_lines)
    }


def unlabeled_body_and_per_label_word_counts(
    prose_lines: list[str],
    configuration,
) -> tuple[int, dict[str, int]]:
    body_words = 0
    per_label_words: dict[str, int] = {}
    open_label: str | None = None
    for line in prose_lines:
        label = matched_reply_label(line, configuration)
        if label:
            open_label = label
            per_label_words.setdefault(label, 0)
        if open_label is None:
            body_words += len(line.split())
        else:
            per_label_words[open_label] += len(line.split())
    return body_words, per_label_words


def text_without_quotations(prose_text: str, configuration) -> str:
    unquoted_lines = [
        line
        for line in prose_text.splitlines()
        if not configuration.syntax_patterns["block_quote_pattern"].match(line)
    ]
    unquoted_text = "\n".join(unquoted_lines)
    unquoted_text = configuration.syntax_patterns["inline_code_pattern"].sub(
        " ", unquoted_text
    )
    return configuration.syntax_patterns["quotation_pattern"].sub(" ", unquoted_text)


class ReplyUnderReview:
    def __init__(self, reply_text: str, configuration=REPLY_FORMAT_CONFIGURATION):
        self.configuration = configuration
        self.text = reply_text
        self.text_without_leading_space = reply_text.lstrip()
        self.prose_lines = prose_lines_outside_visuals(reply_text, configuration)
        self.prose_text = "\n".join(self.prose_lines)
        self.prose_without_quotations = text_without_quotations(
            self.prose_text, configuration
        )
        counted_lines = prose_lines_outside_short_lists(self.prose_lines, configuration)
        self.prose_word_count = sum(len(line.split()) for line in counted_lines)
        self.list_blocks = list_line_blocks(self.prose_lines, configuration)
        self.labels_present = labels_present_in(self.prose_lines, configuration)
        (
            self.unlabeled_body_word_count,
            self.per_label_word_counts,
        ) = unlabeled_body_and_per_label_word_counts(counted_lines, configuration)
        self.labeled_section_word_count = sum(self.per_label_word_counts.values())
        self.label_lines = reply_label_lines(reply_text, configuration)
