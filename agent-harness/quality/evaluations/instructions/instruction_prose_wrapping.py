import re
import textwrap

from instructions.ai_instruction_format import MARKDOWN_PARSER
from instructions.instruction_markdown_frontmatter import parse_instruction_body


def wrap_instruction_prose(text: str) -> str:
    body = parse_instruction_body(text)
    tokens = MARKDOWN_PARSER.parse(body.text)
    blocks = []
    for index, token in enumerate(tokens):
        wrapped_block = _wrapped_instruction_block(tokens, index)
        if wrapped_block is None:
            continue
        blocks.append(wrapped_block)
    metadata = "\n".join(text.splitlines()[: body.first_line_number - 1])
    rendered = (metadata + "\n\n" if metadata else "") + "\n\n".join(blocks) + "\n"
    original_literals = inline_literals(tokens)
    rendered_literals = inline_literals(
        MARKDOWN_PARSER.parse(parse_instruction_body(rendered).text)
    )
    if original_literals != rendered_literals:
        raise ValueError("prose wrapping changed an inline literal or link destination")
    return rendered


def _wrapped_instruction_block(tokens, index):
    token = tokens[index]
    if token.type != "inline":
        return None
    if tokens[index - 1].type == "heading_open":
        return "### " + token.content
    wrapped = textwrap.fill(
        token.content.replace("\n", " "),
        width=120,
        break_long_words=False,
        break_on_hyphens=False,
    )
    lines = wrapped.splitlines()
    _escape_wrapped_markdown_lists(lines, wrapped)
    return "\n".join(lines)


def _escape_wrapped_markdown_lists(lines, wrapped):
    for block in MARKDOWN_PARSER.parse(wrapped):
        if block.type not in {"ordered_list_open", "bullet_list_open"}:
            continue
        row = block.map[0]
        lines[row] = re.sub(r"^(\d+)([.)]) ", r"\1\\\2 ", lines[row])
        lines[row] = re.sub(r"^([-+*]) ", r"\\\1 ", lines[row])


def inline_literals(tokens):
    return [
        (
            child.type,
            child.content if child.type == "code_inline" else child.attrGet("href"),
        )
        for token in tokens
        for child in token.children or []
        if child.type in {"code_inline", "link_open"}
    ]
