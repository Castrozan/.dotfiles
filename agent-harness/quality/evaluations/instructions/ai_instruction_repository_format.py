import re
from pathlib import Path

from instructions.ai_instruction_format import inspect_markdown_instruction
from instructions.instruction_format_diagnostics import InstructionFormatViolation
from instructions.instruction_surface_scanner import (
    REPO_ROOT,
    SOURCEBOT_SKILL_TREE,
    every_linted_markdown_file,
    frontmatter_key_values,
    named_instruction_entrypoint_files,
    skill_definition_files,
    skill_reference_files,
)
from instructions.validation.instruction_repository_validation import (
    validate_duplicate_instruction_names,
    validate_instruction_sources,
    validate_misplaced_skill_markdown,
    validate_noncanonical_skill_references,
    validate_skill_reference_routes,
)

MAXIMUM_INSTRUCTION_DESCRIPTION_WORDS = 35
MAXIMUM_INSTRUCTION_DESCRIPTION_SENTENCES = 2
INSTRUCTION_NAME = re.compile(r"^[a-z][a-z0-9]*(?:-[a-z0-9]+)*$")


def instruction_identity_violations(path: Path) -> list[InstructionFormatViolation]:
    key_values = frontmatter_key_values(path.read_text()) or {}
    name = key_values.get("name", "")
    description = key_values.get("description", "")
    violations = _instruction_name_violations(name)
    expected_name = _expected_instruction_name(path)
    if name and name != expected_name:
        violations.append(
            InstructionFormatViolation(
                "instruction_name",
                None,
                f"name '{name}' does not match '{expected_name}'",
            )
        )
    violations.extend(_instruction_description_violations(description))
    return violations


def _instruction_name_violations(name):
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
    return violations


def _expected_instruction_name(path):
    expected_name = path.parent.name if path.name == "SKILL.md" else path.stem
    if path.parent == SOURCEBOT_SKILL_TREE:
        expected_name = path.parent.parent.name
    if path.name == "core-skill-frontmatter.md":
        expected_name = "core"
    return expected_name


def _instruction_description_violations(description):
    violations = []
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

    metadata_fragment = (
        REPO_ROOT
        / "agent-harness/agent-instructions/core-rules/core-skill-frontmatter.md"
    )
    inspections = {
        path: inspect_markdown_instruction(path.read_text())
        for path in paths
        if path != metadata_fragment
    }
    validate_instruction_sources(inspections, metadata_fragment, add)
    named_files = named_instruction_entrypoint_files()
    for path in named_files:
        for violation in instruction_identity_violations(path):
            add(path, violation)
    validate_duplicate_instruction_names(add)
    validate_misplaced_skill_markdown(add)
    references = skill_reference_files()
    validate_noncanonical_skill_references(
        skill_definition_files() + references, inspections, add
    )
    validate_skill_reference_routes(
        references, inspections, add, INSTRUCTION_NAME.fullmatch
    )
    return dict(sorted(violations.items()))
