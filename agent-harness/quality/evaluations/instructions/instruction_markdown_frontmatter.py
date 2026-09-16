from dataclasses import dataclass

import yaml

from instructions.instruction_format_diagnostics import InstructionFormatViolation


class InstructionMetadataLoader(yaml.SafeLoader):
    def construct_mapping(self, node, deep=False):
        names = set()
        for key, _ in node.value:
            name = self.construct_object(key, deep=deep)
            if not isinstance(name, str) or name in names:
                raise yaml.constructor.ConstructorError(
                    None, None, "expected unique metadata field names", key.start_mark
                )
            names.add(name)
        return super().construct_mapping(node, deep=deep)


@dataclass(frozen=True)
class InstructionBody:
    text: str
    first_line_number: int
    violations: list[InstructionFormatViolation]


def parse_instruction_body(text: str) -> InstructionBody:
    lines = text.removeprefix("\ufeff").splitlines()
    if not lines or lines[0] != "---":
        return InstructionBody("\n".join(lines), 1, [])
    try:
        closing_line = lines.index("---", 1)
    except ValueError:
        return InstructionBody(
            "",
            1,
            [
                InstructionFormatViolation(
                    "instruction_frontmatter", 1, "expected closing ---"
                )
            ],
        )
    violations = []
    try:
        metadata = yaml.load(
            "\n".join(lines[1:closing_line]), InstructionMetadataLoader
        )
        if not isinstance(metadata, dict):
            raise ValueError("expected YAML mapping frontmatter")
    except (yaml.YAMLError, ValueError) as error:
        violations.append(
            InstructionFormatViolation("instruction_frontmatter", 1, str(error))
        )
    return InstructionBody(
        "\n".join(lines[closing_line + 1 :]), closing_line + 2, violations
    )
