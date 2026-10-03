from pathlib import Path

from instructions.ai_instruction_references import (
    noncanonical_skill_reference_paths,
    owning_skill_directory,
    skill_reference_references,
)
from instructions.instruction_format_diagnostics import InstructionFormatViolation
from instructions.instruction_link_targets import instruction_link_violations
from instructions.instruction_markdown_frontmatter import parse_instruction_body
from instructions.instruction_surface_scanner import (
    frontmatter_key_values,
    misplaced_skill_markdown_files,
    skill_definition_files,
)


def validate_instruction_sources(inspections, metadata_fragment, add):
    for path, inspection in list(inspections.items()):
        for violation in inspection.violations + instruction_link_violations(
            path, inspection, inspections
        ):
            add(path, violation)
    metadata = parse_instruction_body(metadata_fragment.read_text())
    for violation in metadata.violations:
        add(metadata_fragment, violation)
    if metadata.text.strip():
        add(
            metadata_fragment,
            InstructionFormatViolation(
                "instruction_frontmatter",
                metadata.first_line_number,
                "expected metadata only in the core frontmatter fragment",
            ),
        )


def validate_duplicate_instruction_names(add):
    names_to_paths: dict[str, list[Path]] = {}
    for path in skill_definition_files():
        name = _instruction_name_for_path(path)
        names_to_paths.setdefault(name, []).append(path)
    for name, name_paths in names_to_paths.items():
        if name and len(name_paths) > 1:
            _report_duplicate_instruction_name(name, name_paths, add)


def _instruction_name_for_path(path):
    return (frontmatter_key_values(path.read_text()) or {}).get("name", "")


def _report_duplicate_instruction_name(name, paths, add):
    for path in paths:
        add(
            path,
            InstructionFormatViolation(
                "instruction_name",
                None,
                f"name '{name}' is not unique",
            ),
        )


def validate_misplaced_skill_markdown(add):
    for path in misplaced_skill_markdown_files():
        add(
            path,
            InstructionFormatViolation(
                "skill_reference_location",
                None,
                "skill-owned instruction Markdown belongs under references/",
            ),
        )


def validate_noncanonical_skill_references(paths, inspections, add):
    for path in paths:
        for token in noncanonical_skill_reference_paths(path, inspections[path]):
            add(
                path,
                InstructionFormatViolation(
                    "skill_reference_path",
                    None,
                    f"'{token}' must be a relative Markdown link from the containing file",
                ),
            )


def validate_skill_reference_routes(references, inspections, add, name_pattern):
    for reference_file in references:
        _validate_reference_route(reference_file, inspections, add, name_pattern)


def _validate_reference_route(reference_file, inspections, add, name_pattern):
    if not name_pattern(reference_file.stem):
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
        return
    relative_reference = reference_file.relative_to(skill_directory).as_posix()
    if relative_reference not in skill_reference_references(
        skill_directory / "SKILL.md", inspections[skill_directory / "SKILL.md"]
    ):
        add(
            reference_file,
            InstructionFormatViolation(
                "skill_reference_route",
                None,
                f"SKILL.md does not route '{relative_reference}'",
            ),
        )
