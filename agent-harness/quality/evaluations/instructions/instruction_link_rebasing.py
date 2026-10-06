import posixpath
from pathlib import PurePosixPath
from typing import NamedTuple
from urllib.parse import quote, unquote, urljoin, urlsplit, urlunsplit

from markdown_it import MarkdownIt
from markdown_it.rules_inline import StateInline, link

from instructions.instruction_markdown_frontmatter import (
    InstructionBody,
    parse_instruction_body,
)


class LinkRebasingContext(NamedTuple):
    body: InstructionBody
    source: PurePosixPath
    deployed: PurePosixPath
    destinations: dict[PurePosixPath, PurePosixPath]
    source_lines: list[str]
    line_offsets: list[int]
    content_lines: list[str]


def capture_link_destination(state: StateInline, silent: bool) -> bool:
    source_position = state.pos
    token_count = len(state.tokens)
    label_end = _link_label_end(state, source_position)
    if not link(state, silent):
        return False
    if not _link_destination_span_is_needed(state, silent, label_end):
        return True
    destination_start = _link_destination_start(state.src, label_end)
    destination = state.md.helpers.parseLinkDestination(
        state.src, destination_start, len(state.src)
    )
    if destination.ok:
        _record_link_destination_span(
            state.tokens[token_count:], destination_start, destination.pos
        )
    return True


def _link_destination_start(source, label_end):
    destination_start = label_end + 2
    while destination_start < len(source) and source[destination_start] in " \t\n":
        destination_start += 1
    return destination_start


def _record_link_destination_span(tokens, destination_start, destination_end):
    opening = next(token for token in tokens if token.type == "link_open")
    opening.meta["destination_span"] = (destination_start, destination_end)


def _link_label_end(state: StateInline, source_position: int) -> int:
    if state.src[source_position] == "[":
        return state.md.helpers.parseLinkLabel(state, source_position, True)
    return -1


def _link_destination_span_is_needed(state: StateInline, silent: bool, label_end: int):
    return not (
        silent or label_end < 0 or state.src[label_end + 1 : label_end + 2] != "("
    )


LINK_SOURCE_PARSER = MarkdownIt("commonmark")
LINK_SOURCE_PARSER.inline.ruler.at("link", capture_link_destination)


def deployed_link_target(
    target: str,
    source: PurePosixPath,
    deployed: PurePosixPath,
    destinations: dict[PurePosixPath, PurePosixPath],
) -> str:
    destination = urlsplit(urljoin(source.as_uri(), target))
    if destination.scheme != "file":
        return target
    path = PurePosixPath(unquote(destination.path, errors="strict"))
    for ancestor in (path, *path.parents):
        if ancestor in destinations:
            projected = destinations[ancestor] / path.relative_to(ancestor)
            relative = (
                ""
                if projected == deployed
                else posixpath.relpath(projected, deployed.parent)
            )
            return urlunsplit(
                (
                    "",
                    "",
                    quote(relative, safe="/._-~"),
                    destination.query,
                    destination.fragment,
                )
            )
    raise ValueError(f"no deployed destination for instruction link: {path}")


def rebase_instruction_links(
    text: str,
    source: PurePosixPath,
    deployed: PurePosixPath,
    destinations: dict[PurePosixPath, PurePosixPath],
) -> str:
    body = parse_instruction_body(text)
    if body.violations:
        raise ValueError("cannot rebase instruction links with invalid frontmatter")
    source_lines = text.splitlines(keepends=True)
    line_offsets = [0]
    for line in source_lines:
        line_offsets.append(line_offsets[-1] + len(line))
    context = LinkRebasingContext(
        body, source, deployed, destinations, source_lines, line_offsets, []
    )
    replacements = []
    for token in LINK_SOURCE_PARSER.parse(body.text):
        replacements.extend(_link_replacements_for_token(token, context))
    for start, end, replacement in sorted(replacements, reverse=True):
        text = text[:start] + replacement + text[end:]
    return text


def _link_replacements_for_token(token, context):
    if token.type != "inline":
        return []
    context = context._replace(content_lines=token.content.split("\n"))
    replacements = []
    for child in token.children or []:
        replacement = _link_replacement_for_child(token, child, context)
        if replacement is not None:
            replacements.append(replacement)
    return replacements


def _link_replacement_for_child(token, child, context):
    if not _has_link_destination_span(child):
        return None
    target = child.attrGet("href") or ""
    replacement = deployed_link_target(
        target, context.source, context.deployed, context.destinations
    )
    if replacement == target:
        return None
    start, end = child.meta["destination_span"]
    source_offset = _link_source_offset(token, context, start)
    if token.content[start:end].startswith("<"):
        replacement = f"<{replacement}>"
    return source_offset, source_offset + end - start, replacement


def _has_link_destination_span(child):
    return child.type == "link_open" and "destination_span" in child.meta


def _link_source_offset(token, context, start):
    preceding = token.content[:start]
    row = preceding.count("\n")
    column = len(preceding.rsplit("\n", 1)[-1])
    source_row = context.body.first_line_number - 1 + token.map[0] + row
    content_column = context.source_lines[source_row].find(context.content_lines[row])
    if content_column < 0:
        raise ValueError("cannot locate parsed link in its source line")
    return context.line_offsets[source_row] + content_column + column
