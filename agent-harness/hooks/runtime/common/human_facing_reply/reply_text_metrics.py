from reply_format_configuration import REPLY_FORMAT_CONFIGURATION
from reply_markdown_document import ReplyMarkdownDocument
from reply_quotations import text_outside_quotations


def body_and_label_word_counts(document, counted_lines):
    body_words = 0
    per_label_words = {}
    labels_by_line = {label.line_index: label.label for label in document.labels}
    open_label = None
    for index in sorted(counted_lines):
        if index in labels_by_line:
            open_label = labels_by_line[index]
            per_label_words.setdefault(open_label, 0)
        word_count = len(document.source_lines[index].split())
        if open_label is None:
            body_words += word_count
        else:
            per_label_words[open_label] += word_count
    return body_words, per_label_words


class ReplyUnderReview:
    def __init__(self, reply_text: str, configuration=REPLY_FORMAT_CONFIGURATION):
        self.configuration = configuration
        document = ReplyMarkdownDocument(reply_text, configuration)
        self.list_blocks = document.lists
        self.label_lines = document.labels
        self.labels_present = {label.label for label in document.labels}
        counted_lines = set(document.prose_line_indices)
        for block in document.lists:
            if block.is_exempt(configuration):
                counted_lines.difference_update(block.line_indices)
        self.prose_word_count = sum(
            len(document.source_lines[index].split()) for index in counted_lines
        )
        self.unlabeled_body_word_count, self.per_label_word_counts = (
            body_and_label_word_counts(document, counted_lines)
        )
        self.labeled_section_word_count = sum(self.per_label_word_counts.values())
        self.inline_blocks = document.content.inline_blocks
        self.opening_text = document.content.opening_text.translate(
            str.maketrans(
                dict.fromkeys(configuration.syntax["apostrophe_characters"], "'")
            )
        )
        self.prose_without_quotations = text_outside_quotations(
            "\n".join(document.content.style_blocks),
            configuration.syntax["quotation_pairs"],
        )
