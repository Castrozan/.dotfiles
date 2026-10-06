import re
from functools import cache

from reply_markdown_inline import ReplyInlineContent, extract_reply_labels
from reply_markdown_lists import extract_reply_lists


BOXED_TABLE_BORDER_PATTERN = re.compile(
    r"^[ \t>]*(?:\+(?:[-=]+\+)+|[┌┏╔├┣╠└┗╚][─━═]+"
    r"(?:[┬┳╦┼╋╬┴┻╩][─━═]+)*[┐┓╗┤┫╣┘┛╝])[ \t]*$"
)
BOXED_TABLE_ROW_PATTERN = re.compile(r"^[ \t>]*[|│┃║].*[|│┃║][ \t]*$")


@cache
def reply_markdown_parser():
    from markdown_it import MarkdownIt

    return MarkdownIt("commonmark").enable(["table", "strikethrough"])


def extract_table_first_columns(tokens):
    columns = []
    inside_table = False
    first_cell = False
    for token in tokens:
        inside_table, first_cell = _update_table_context(
            token.type, columns, inside_table, first_cell
        )
        if token.type == "inline" and inside_table and first_cell:
            columns[-1].append(_first_column_cell_text(token.children))
            first_cell = False
    return columns


def _update_table_context(token_type, columns, inside_table, first_cell):
    if token_type == "table_open":
        columns.append([])
        inside_table = True
    elif token_type == "table_close":
        inside_table = False
    elif token_type == "tr_open":
        first_cell = True
    return inside_table, first_cell


def _first_column_cell_text(children):
    return "".join(
        child.content
        for child in children or []
        if child.type in ("text", "code_inline")
    ).strip()


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
            opening_seen = self._record_inline_content(
                content, token.map, quote_depth, list_depth, table_depth, opening_seen
            )

    def _record_inline_content(
        self, content, source_map, quote_depth, list_depth, table_depth, opening_seen
    ):
        if not quote_depth:
            self.style_blocks.append(content.outside_code)
        if not opening_seen:
            self.opening_text = content.outside_code.lstrip()
            opening_seen = True
        if _is_outside_markdown_structure(quote_depth, list_depth, table_depth):
            self.label_line_indices.update(range(*source_map))
        return opening_seen


def _is_outside_markdown_structure(quote_depth, list_depth, table_depth):
    return not (quote_depth or list_depth or table_depth)


def label_containing_table(document):
    if not document.labels:
        return None
    first_label_line = document.labels[0].line_index
    table_lines = table_start_line_indices(document.tokens, first_label_line)
    labels_by_line = {label.line_index: label.label for label in document.labels}
    current_label = None
    for index in range(first_label_line, len(document.source_lines)):
        if index in labels_by_line:
            current_label = labels_by_line[index]
        if index in table_lines or is_boxed_table_border(document.source_lines, index):
            return current_label
    return None


def is_boxed_table_border(source_lines, index):
    line = source_lines[index]
    if not BOXED_TABLE_BORDER_PATTERN.fullmatch(line):
        return False
    if line.count("+") > 2 or any(join in line for join in "┬┳╦┼╋╬┴┻╩"):
        return True
    return (
        0 < index < len(source_lines) - 1
        and BOXED_TABLE_ROW_PATTERN.fullmatch(source_lines[index - 1])
        and BOXED_TABLE_ROW_PATTERN.fullmatch(source_lines[index + 1])
    )


def table_start_line_indices(tokens, first_label_line):
    indices = set()
    for token in tokens:
        if not token.map or token.map[0] < first_label_line:
            continue
        if token.type == "table_open" or (
            token.type in ("fence", "code_block")
            and any(
                content.type == "table_open"
                for content in reply_markdown_parser().parse(token.content)
            )
        ):
            indices.add(token.map[0])
    return indices


class ReplyMarkdownDocument:
    def __init__(self, text, configuration):
        parser = reply_markdown_parser()
        tokens = parser.parse(text)
        self.tokens = tokens
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
        self.label_containing_table = label_containing_table(self)
