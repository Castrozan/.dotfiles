from dataclasses import dataclass, field
import re

from github_slugger import GithubSlugger, slug
from markdown_it import MarkdownIt
from markdown_it.token import Token

from instructions.instruction_format_diagnostics import InstructionFormatViolation
from instructions.instruction_markdown_frontmatter import parse_instruction_body
from instructions.validation.instruction_block_validation import (
    is_instruction_heading,
    is_instruction_paragraph,
    record_heading_transition,
    report_empty_instruction_section,
    report_unconsumed_instruction_lines,
    valid_instruction_block,
)

MAXIMUM_INSTRUCTION_PROSE_LINES = 150
MAXIMUM_SECTION_PROSE_LINES = 20
MAXIMUM_PARAGRAPH_PROSE_LINES = 6
MARKDOWN_PARSER = MarkdownIt("commonmark").enable(["table", "strikethrough"])
PROSE_TOKEN_TYPES = frozenset(
    {"text", "code_inline", "softbreak", "link_open", "link_close"}
)


@dataclass(frozen=True)
class InstructionLink:
    line_number: int
    target: str


@dataclass
class InstructionInspection:
    violations: list[InstructionFormatViolation] = field(default_factory=list)
    anchors: list[str] = field(default_factory=list)
    links: list[InstructionLink] = field(default_factory=list)

    def reject(self, rule: str, line_number: int, detail: str) -> None:
        self.violations.append(InstructionFormatViolation(rule, line_number, detail))


def inspect_inline_prose(
    token: Token, first_line_number: int, inspection: InstructionInspection
) -> None:
    line_number = first_line_number
    for child in token.children or []:
        line_number += _inspect_inline_prose_child(child, line_number, inspection)


def _inspect_inline_prose_child(child, line_number, inspection):
    if _inline_prose_child_is_invalid(child):
        inspection.reject(
            "instruction_inline_prose",
            line_number,
            "expected prose, inline code, or inline links; delimit literal angle brackets with backticks",
        )
    if child.type == "link_open":
        inspection.links.append(
            InstructionLink(line_number, child.attrGet("href") or "")
        )
    return 1 if child.type == "softbreak" else child.content.count("\n")


def _inline_prose_child_is_invalid(child):
    return child.type not in PROSE_TOKEN_TYPES or (
        child.type == "text" and any(character in child.content for character in "<>")
    )


def inspect_heading_anchors(
    tokens: list[Token], first_line_number: int, inspection: InstructionInspection
) -> None:
    heading_names = set()
    slugger = GithubSlugger()
    for index, token in enumerate(tokens):
        if token.type != "heading_open":
            continue
        heading = tokens[index + 1]
        text = _heading_text(heading)
        anchor = slugger.slug(text)
        name = slug(text) if re.search(r"-[0-9]+$", anchor) else anchor
        inspection.anchors.append(anchor)
        if _heading_anchor_is_invalid(text, name, heading_names):
            inspection.reject(
                "instruction_heading_anchor",
                first_line_number + token.map[0],
                "expected a nonempty unique heading anchor",
            )
        heading_names.add(name)


def _heading_anchor_is_invalid(text, name, heading_names):
    return not text.strip() or not name or name in heading_names


def _heading_text(heading):
    return "".join(child.content for child in heading.children or [])


def inspect_markdown_instruction(text: str) -> InstructionInspection:
    body = parse_instruction_body(text)
    inspection = InstructionInspection(violations=list(body.violations))
    tokens = MARKDOWN_PARSER.parse(body.text)
    inspect_heading_anchors(tokens, body.first_line_number, inspection)
    return _inspect_markdown_blocks(body, tokens, inspection)


def _inspect_markdown_blocks(body, tokens, inspection):
    consumed_lines = set()
    section_line_number = 0
    section_prose_lines = 0
    total_prose_lines = 0
    for index in range(0, len(tokens), 3):
        opening = tokens[index]
        following = tokens[index + 1 : index + 3]
        line_number = _instruction_block_line_number(body, opening)
        heading = is_instruction_heading(opening)
        paragraph = is_instruction_paragraph(opening, section_line_number)
        if not valid_instruction_block(opening, following, heading, paragraph):
            inspection.reject(
                "instruction_section_structure",
                line_number,
                "expected a ### heading followed by nonempty prose",
            )
            return inspection
        if heading:
            record_heading_transition(
                inspection, section_line_number, section_prose_lines
            )
            section_line_number = line_number
            section_prose_lines = 0
        else:
            section_prose_lines, total_prose_lines = _record_paragraph_prose(
                opening,
                line_number,
                section_prose_lines,
                total_prose_lines,
                inspection,
            )
        inspect_inline_prose(following[0], line_number, inspection)
        consumed_lines.update(range(*opening.map))
    report_unconsumed_instruction_lines(body, consumed_lines, inspection)
    _report_final_prose_limits(
        body, section_line_number, section_prose_lines, total_prose_lines, inspection
    )
    return inspection


def _instruction_block_line_number(body, opening):
    return body.first_line_number + (opening.map or [0])[0]


def _record_paragraph_prose(
    opening, line_number, section_prose_lines, total_prose_lines, inspection
):
    prose_lines = opening.map[1] - opening.map[0]
    if prose_lines > MAXIMUM_PARAGRAPH_PROSE_LINES:
        inspection.reject(
            "instruction_paragraph_prose_line_limit",
            line_number,
            f"expected at most {MAXIMUM_PARAGRAPH_PROSE_LINES} prose lines per paragraph",
        )
    previous_section_lines = section_prose_lines
    section_prose_lines += prose_lines
    total_prose_lines += prose_lines
    if previous_section_lines <= MAXIMUM_SECTION_PROSE_LINES < section_prose_lines:
        inspection.reject(
            "instruction_section_prose_line_limit",
            line_number,
            f"expected at most {MAXIMUM_SECTION_PROSE_LINES} prose lines per section",
        )
    return section_prose_lines, total_prose_lines


def _report_final_prose_limits(
    body, section_line_number, section_prose_lines, total_prose_lines, inspection
):
    report_empty_instruction_section(
        body, section_line_number, section_prose_lines, inspection
    )
    if total_prose_lines > MAXIMUM_INSTRUCTION_PROSE_LINES:
        inspection.reject(
            "instruction_prose_line_limit",
            body.first_line_number,
            f"expected at most {MAXIMUM_INSTRUCTION_PROSE_LINES} prose lines per instruction",
        )
