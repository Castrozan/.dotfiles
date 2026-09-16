import posixpath
from pathlib import PurePosixPath
from urllib.parse import quote, unquote, urljoin, urlsplit, urlunsplit

from markdown_it import MarkdownIt
from markdown_it.rules_inline import StateInline, link

from instructions.instruction_markdown_frontmatter import parse_instruction_body


def capture_link_destination(state: StateInline, silent: bool) -> bool:
    source_position = state.pos
    token_count = len(state.tokens)
    label_end = (
        state.md.helpers.parseLinkLabel(state, source_position, True)
        if state.src[source_position] == "["
        else -1
    )
    if not link(state, silent):
        return False
    if silent or label_end < 0 or state.src[label_end + 1 : label_end + 2] != "(":
        return True
    destination_start = label_end + 2
    while (
        destination_start < len(state.src) and state.src[destination_start] in " \t\n"
    ):
        destination_start += 1
    destination = state.md.helpers.parseLinkDestination(
        state.src, destination_start, len(state.src)
    )
    if destination.ok:
        opening = next(
            token for token in state.tokens[token_count:] if token.type == "link_open"
        )
        opening.meta["destination_span"] = (destination_start, destination.pos)
    return True


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
    replacements = []
    for token in LINK_SOURCE_PARSER.parse(body.text):
        if token.type != "inline":
            continue
        content_lines = token.content.split("\n")
        for child in token.children or []:
            if child.type != "link_open" or "destination_span" not in child.meta:
                continue
            target = child.attrGet("href") or ""
            replacement = deployed_link_target(target, source, deployed, destinations)
            if replacement == target:
                continue
            start, end = child.meta["destination_span"]
            preceding = token.content[:start]
            row = preceding.count("\n")
            column = len(preceding.rsplit("\n", 1)[-1])
            source_row = body.first_line_number - 1 + token.map[0] + row
            content_column = source_lines[source_row].find(content_lines[row])
            if content_column < 0:
                raise ValueError("cannot locate parsed link in its source line")
            absolute_start = line_offsets[source_row] + content_column + column
            if token.content[start:end].startswith("<"):
                replacement = f"<{replacement}>"
            replacements.append(
                (absolute_start, absolute_start + end - start, replacement)
            )
    for start, end, replacement in sorted(replacements, reverse=True):
        text = text[:start] + replacement + text[end:]
    return text
