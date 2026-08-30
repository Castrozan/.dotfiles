import re
from dataclasses import dataclass

MAXIMUM_INSTRUCTION_PROSE_LINES = 150
MAXIMUM_XML_SECTION_PROSE_LINES = 20
XML_DELIMITER = re.compile(r"^\s*<(/?)([^<>]+)>\s*$")
XML_TAG_NAME = re.compile(r"^[a-z][a-z0-9]*(?:_[a-z0-9]+)*$")
INLINE_XML_TAG_REFERENCE = re.compile(r"`<(/?)([A-Za-z][A-Za-z0-9_-]*)>`")


@dataclass(frozen=True)
class InstructionFormatViolation:
    rule: str
    line_number: int | None
    detail: str

    def render(self) -> str:
        location = f"line {self.line_number}: " if self.line_number else ""
        return f"{self.rule}: {location}{self.detail}"


def instruction_body_lines(text: str) -> list[tuple[int, str]]:
    lines = text.splitlines()
    body_start = 0
    if lines and lines[0] == "---":
        try:
            body_start = lines.index("---", 1) + 1
        except ValueError:
            body_start = 0
    return list(enumerate(lines[body_start:], body_start + 1))


def instruction_format_violations(text: str) -> list[InstructionFormatViolation]:
    violations = []
    open_sections: list[dict[str, str | int | bool]] = []
    prose_line_count = 0
    for line_number, line in instruction_body_lines(text):
        stripped = line.strip()
        delimiter = XML_DELIMITER.fullmatch(line)
        if delimiter:
            closing = bool(delimiter.group(1))
            tag_name = delimiter.group(2)
            if not XML_TAG_NAME.fullmatch(tag_name):
                violations.append(
                    InstructionFormatViolation(
                        "xml_tag_name",
                        line_number,
                        f"<{tag_name}> must use lowercase snake_case",
                    )
                )
            if closing:
                if not open_sections or open_sections[-1]["name"] != tag_name:
                    violations.append(
                        InstructionFormatViolation(
                            "xml_tag_balance",
                            line_number,
                            f"</{tag_name}> does not close the current section",
                        )
                    )
                else:
                    open_sections.pop()
            else:
                if open_sections:
                    violations.append(
                        InstructionFormatViolation(
                            "nested_xml_section",
                            line_number,
                            f"<{tag_name}> is nested inside <{open_sections[-1]['name']}>",
                        )
                    )
                open_sections.append(
                    {"name": tag_name, "prose_lines": 0, "limit_reported": False}
                )
            continue
        if stripped:
            prose_line_count += 1
            if not open_sections:
                violations.append(
                    InstructionFormatViolation(
                        "prose_outside_xml_section",
                        line_number,
                        "body prose must be enclosed by a standalone XML section",
                    )
                )
                continue
            section = open_sections[-1]
            section["prose_lines"] = int(section["prose_lines"]) + 1
            if (
                int(section["prose_lines"]) > MAXIMUM_XML_SECTION_PROSE_LINES
                and not section["limit_reported"]
            ):
                section["limit_reported"] = True
                violations.append(
                    InstructionFormatViolation(
                        "xml_section_prose_line_limit",
                        line_number,
                        f"<{section['name']}> exceeds "
                        f"{MAXIMUM_XML_SECTION_PROSE_LINES} prose lines",
                    )
                )
        elif open_sections:
            violations.append(
                InstructionFormatViolation(
                    "blank_line_inside_xml_section",
                    line_number,
                    f"<{open_sections[-1]['name']}> contains a blank line",
                )
            )
    for section in reversed(open_sections):
        violations.append(
            InstructionFormatViolation(
                "xml_tag_balance", None, f"<{section['name']}> is not closed"
            )
        )
    if prose_line_count > MAXIMUM_INSTRUCTION_PROSE_LINES:
        violations.append(
            InstructionFormatViolation(
                "instruction_prose_line_limit",
                None,
                f"file has {prose_line_count} prose lines; maximum is "
                f"{MAXIMUM_INSTRUCTION_PROSE_LINES}",
            )
        )
    return violations


def declared_xml_tags(text: str) -> set[str]:
    return {
        delimiter.group(2)
        for _, line in instruction_body_lines(text)
        if (delimiter := XML_DELIMITER.fullmatch(line))
        and not delimiter.group(1)
        and XML_TAG_NAME.fullmatch(delimiter.group(2))
    }


def inline_xml_tag_references(text: str) -> list[tuple[int, str]]:
    return [
        (line_number, matched.group(2))
        for line_number, line in instruction_body_lines(text)
        for matched in INLINE_XML_TAG_REFERENCE.finditer(line)
    ]


def xml_tag_structure_error(text: str) -> str | None:
    balance_violations = [
        violation
        for violation in instruction_format_violations(text)
        if violation.rule in {"nested_xml_section", "xml_tag_balance"}
    ]
    return balance_violations[0].detail if balance_violations else None


def unclosed_code_fence_count(text: str) -> int:
    return sum(1 for line in text.splitlines() if line.startswith("```")) % 2
