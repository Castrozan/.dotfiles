from functools import cache

from reply_markdown_inline import ReplyInlineContent, extract_reply_labels
from reply_markdown_lists import extract_reply_lists


@cache
def reply_markdown_parser():
    from markdown_it import MarkdownIt

    return MarkdownIt("commonmark").enable(["table", "strikethrough"])


def extract_table_first_columns(tokens):
    columns = []
    inside_table = False
    first_cell = False
    for token in tokens:
        if token.type == "table_open":
            columns.append([])
            inside_table = True
        elif token.type == "table_close":
            inside_table = False
        elif token.type == "tr_open":
            first_cell = True
        elif token.type == "inline" and inside_table and first_cell:
            columns[-1].append(
                "".join(
                    child.content
                    for child in token.children or []
                    if child.type in ("text", "code_inline")
                ).strip()
            )
            first_cell = False
    return columns


def visual_line_indices(tokens, source_lines, configuration):
    indices = {
        index
        for token in tokens
        if token.type in ("fence", "code_block", "table_open")
        for index in range(*token.map)
    }
    indices.update(
        index
        for index, line in enumerate(source_lines)
        if configuration.tree_branch_pattern.match(line)
    )
    return indices


class ReplyMarkdownContent:
    def __init__(self, tokens):
        self.inline_blocks = []
        self.style_blocks = []
        self.label_line_indices = set()
        self.opening_text = ""
        opening_seen = False
        quote_depth = 0
        list_depth = 0
        table_depth = 0
        for token in tokens:
            quote_depth += (token.type == "blockquote_open") - (
                token.type == "blockquote_close"
            )
            list_depth += (token.type == "list_item_open") - (
                token.type == "list_item_close"
            )
            table_depth += (token.type == "table_open") - (token.type == "table_close")
            if token.type in ("fence", "code_block", "table_open", "blockquote_open"):
                opening_seen = True
            if token.type != "inline":
                continue
            content = ReplyInlineContent(token.children or [])
            self.inline_blocks.append(content)
            if not quote_depth:
                self.style_blocks.append(content.outside_code)
            if not opening_seen:
                self.opening_text = content.outside_code.lstrip()
                opening_seen = True
            if not (quote_depth or list_depth or table_depth):
                self.label_line_indices.update(range(*token.map))


class ReplyMarkdownDocument:
    def __init__(self, text, configuration):
        parser = reply_markdown_parser()
        tokens = parser.parse(text)
        self.source_lines = text.replace("\r\n", "\n").replace("\r", "\n").split("\n")
        visual_lines = visual_line_indices(tokens, self.source_lines, configuration)
        self.prose_line_indices = {
            index
            for index, line in enumerate(self.source_lines)
            if line.strip() and index not in visual_lines
        }
        self.lists = extract_reply_lists(
            tokens, self.source_lines, self.prose_line_indices
        )
        self.table_first_columns = extract_table_first_columns(tokens)
        self.content = ReplyMarkdownContent(tokens)
        self.labels = extract_reply_labels(
            self.source_lines,
            self.content.label_line_indices & self.prose_line_indices,
            configuration,
            parser,
        )
