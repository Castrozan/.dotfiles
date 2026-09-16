from dataclasses import dataclass, field
import re

from github_slugger import GithubSlugger, slug
from markdown_it import MarkdownIt
from markdown_it.token import Token

from instructions.instruction_format_diagnostics import InstructionFormatViolation
from instructions.instruction_markdown_frontmatter import parse_instruction_body

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
        if child.type not in PROSE_TOKEN_TYPES or (
            child.type == "text"
            and any(character in child.content for character in "<>")
        ):
            inspection.reject(
                "instruction_inline_prose",
                line_number,
                "expected prose, inline code, or inline links; delimit literal angle brackets with backticks",
            )
        if child.type == "link_open":
            inspection.links.append(
                InstructionLink(line_number, child.attrGet("href") or "")
            )
        line_number += 1 if child.type == "softbreak" else child.content.count("\n")


def inspect_heading_anchors(
    tokens: list[Token], first_line_number: int, inspection: InstructionInspection
) -> None:
    heading_names = set()
    slugger = GithubSlugger()
    for index, token in enumerate(tokens):
        if token.type != "heading_open":
            continue
        heading = tokens[index + 1]
        text = "".join(child.content for child in heading.children or [])
        anchor = slugger.slug(text)
        name = slug(text) if re.search(r"-[0-9]+$", anchor) else anchor
        inspection.anchors.append(anchor)
        if not text.strip() or not name or name in heading_names:
            inspection.reject(
                "instruction_heading_anchor",
                first_line_number + token.map[0],
                "expected a nonempty unique heading anchor",
            )
        heading_names.add(name)


def inspect_markdown_instruction(text: str) -> InstructionInspection:
    body = parse_instruction_body(text)
    inspection = InstructionInspection(violations=list(body.violations))
    tokens = MARKDOWN_PARSER.parse(body.text)
    inspect_heading_anchors(tokens, body.first_line_number, inspection)
    consumed_lines = set()
    section_line_number = 0
    section_prose_lines = 0
    total_prose_lines = 0
    for index in range(0, len(tokens), 3):
        opening = tokens[index]
        following = tokens[index + 1 : index + 3]
        line_number = body.first_line_number + (opening.map or [0])[0]
        heading = opening.type == "heading_open" and opening.tag == "h3"
        paragraph = opening.type == "paragraph_open" and section_line_number > 0
        if (
            not (heading or paragraph)
            or opening.level != 0
            or len(following) != 2
            or following[0].type != "inline"
            or not following[0].content.strip()
            or following[1].type != ("heading_close" if heading else "paragraph_close")
        ):
            inspection.reject(
                "instruction_section_structure",
                line_number,
                "expected a ### heading followed by nonempty prose",
            )
            return inspection
        if heading:
            if section_line_number and not section_prose_lines:
                inspection.reject(
                    "instruction_section_structure",
                    section_line_number,
                    "expected prose after heading",
                )
            section_line_number = line_number
            section_prose_lines = 0
        else:
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
            if (
                previous_section_lines
                <= MAXIMUM_SECTION_PROSE_LINES
                < section_prose_lines
            ):
                inspection.reject(
                    "instruction_section_prose_line_limit",
                    line_number,
                    f"expected at most {MAXIMUM_SECTION_PROSE_LINES} prose lines per section",
                )
        inspect_inline_prose(following[0], line_number, inspection)
        consumed_lines.update(range(*opening.map))
    for row, line in enumerate(body.text.splitlines()):
        if line.strip() and row not in consumed_lines:
            inspection.reject(
                "instruction_source_coverage",
                body.first_line_number + row,
                "expected a heading or prose paragraph",
            )
    if not section_line_number or not section_prose_lines:
        inspection.reject(
            "instruction_section_structure",
            section_line_number or body.first_line_number,
            "expected a ### heading followed by nonempty prose",
        )
    if total_prose_lines > MAXIMUM_INSTRUCTION_PROSE_LINES:
        inspection.reject(
            "instruction_prose_line_limit",
            body.first_line_number,
            f"expected at most {MAXIMUM_INSTRUCTION_PROSE_LINES} prose lines per instruction",
        )
    return inspection
