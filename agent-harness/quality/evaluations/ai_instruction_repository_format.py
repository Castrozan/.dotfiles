import re
from pathlib import Path

from ai_instruction_format import (
    InstructionFormatViolation,
    XML_TAG_NAME,
    declared_xml_tags,
    inline_xml_tag_references,
    instruction_format_violations,
)
from ai_instruction_references import (
    noncanonical_skill_reference_paths,
    owning_skill_directory,
    skill_reference_references,
    unresolved_skill_references,
)
from instruction_surface_scanner import (
    REPO_ROOT,
    SOURCEBOT_SKILL_TREE,
    every_linted_markdown_file,
    frontmatter_key_values,
    misplaced_skill_markdown_files,
    named_instruction_entrypoint_files,
    skill_definition_files,
    skill_reference_files,
)

MAXIMUM_INSTRUCTION_DESCRIPTION_WORDS = 35
MAXIMUM_INSTRUCTION_DESCRIPTION_SENTENCES = 2
INSTRUCTION_NAME = re.compile(r"^[a-z][a-z0-9]*(?:-[a-z0-9]+)*$")


def instruction_identity_violations(path: Path) -> list[InstructionFormatViolation]:
    key_values = frontmatter_key_values(path.read_text()) or {}
    name = key_values.get("name", "")
    description = key_values.get("description", "")
    violations = []
    if not name:
        violations.append(
            InstructionFormatViolation(
                "instruction_name", None, "named instruction has no name"
            )
        )
    elif not INSTRUCTION_NAME.fullmatch(name):
        violations.append(
            InstructionFormatViolation(
                "instruction_name",
                None,
                f"name '{name}' must use lowercase kebab-case",
            )
        )
    expected_name = path.parent.name if path.name == "SKILL.md" else path.stem
    if path.parent == SOURCEBOT_SKILL_TREE:
        expected_name = path.parent.parent.name
    if path.name == "core-skill-frontmatter.md":
        expected_name = "core"
    if name and name != expected_name:
        violations.append(
            InstructionFormatViolation(
                "instruction_name",
                None,
                f"name '{name}' does not match '{expected_name}'",
            )
        )
    if not description:
        violations.append(
            InstructionFormatViolation(
                "instruction_description", None, "named instruction has no description"
            )
        )
        return violations
    word_count = len(description.split())
    sentences = [
        sentence for sentence in re.split(r"(?<=[.!?])\s+", description) if sentence
    ]
    if word_count > MAXIMUM_INSTRUCTION_DESCRIPTION_WORDS:
        violations.append(
            InstructionFormatViolation(
                "instruction_description",
                None,
                f"description has {word_count} words; maximum is "
                f"{MAXIMUM_INSTRUCTION_DESCRIPTION_WORDS}",
            )
        )
    if len(sentences) > MAXIMUM_INSTRUCTION_DESCRIPTION_SENTENCES:
        violations.append(
            InstructionFormatViolation(
                "instruction_description",
                None,
                f"description has {len(sentences)} sentences; maximum is "
                f"{MAXIMUM_INSTRUCTION_DESCRIPTION_SENTENCES}",
            )
        )
    return violations


def repository_instruction_format_violations() -> dict[str, list[str]]:
    paths = every_linted_markdown_file()
    violations: dict[str, list[str]] = {}

    def add(path: Path, violation: InstructionFormatViolation) -> None:
        relative = str(path.relative_to(REPO_ROOT))
        violations.setdefault(relative, []).append(violation.render())

    for path in paths:
        for violation in instruction_format_violations(path.read_text()):
            add(path, violation)
    named_files = named_instruction_entrypoint_files()
    for path in named_files:
        for violation in instruction_identity_violations(path):
            add(path, violation)
    names_to_paths: dict[str, list[Path]] = {}
    for path in skill_definition_files():
        name = (frontmatter_key_values(path.read_text()) or {}).get("name", "")
        names_to_paths.setdefault(name, []).append(path)
    for name, name_paths in names_to_paths.items():
        if name and len(name_paths) > 1:
            for path in name_paths:
                add(
                    path,
                    InstructionFormatViolation(
                        "instruction_name",
                        None,
                        f"name '{name}' is not unique",
                    ),
                )
    for path in misplaced_skill_markdown_files():
        add(
            path,
            InstructionFormatViolation(
                "skill_reference_location",
                None,
                "skill-owned instruction Markdown belongs under references/",
            ),
        )
    references = skill_reference_files()
    for path in skill_definition_files() + references:
        for reference in unresolved_skill_references(path):
            add(
                path,
                InstructionFormatViolation(
                    "skill_reference_path",
                    None,
                    f"'{reference}' does not resolve from the skill root",
                ),
            )
        for token in noncanonical_skill_reference_paths(path):
            add(
                path,
                InstructionFormatViolation(
                    "skill_reference_path",
                    None,
                    f"'{token}' must be skill-root-relative",
                ),
            )
    for reference_file in references:
        if not INSTRUCTION_NAME.fullmatch(reference_file.stem):
            add(
                reference_file,
                InstructionFormatViolation(
                    "instruction_name",
                    None,
                    "reference filename must use lowercase kebab-case",
                ),
            )
        skill_directory = owning_skill_directory(reference_file)
        if skill_directory is None:
            continue
        relative_reference = reference_file.relative_to(skill_directory).as_posix()
        if relative_reference not in skill_reference_references(
            skill_directory / "SKILL.md"
        ):
            add(
                reference_file,
                InstructionFormatViolation(
                    "skill_reference_route",
                    None,
                    f"SKILL.md does not route '{relative_reference}'",
                ),
            )
    declared_tags = set().union(
        *(declared_xml_tags(path.read_text()) for path in paths)
    )
    for path in paths:
        for line_number, tag_name in inline_xml_tag_references(path.read_text()):
            if not XML_TAG_NAME.fullmatch(tag_name):
                detail = f"inline <{tag_name}> reference must use lowercase snake_case"
            elif tag_name not in declared_tags:
                detail = f"inline <{tag_name}> reference has no declared section"
            else:
                continue
            add(
                path,
                InstructionFormatViolation("xml_tag_reference", line_number, detail),
            )
    return dict(sorted(violations.items()))
