import pytest
from instructions.ai_instruction_format import inspect_markdown_instruction

from instructions.ai_instruction_references import noncanonical_skill_reference_paths
from instructions.ai_instruction_repository_format import (
    repository_instruction_format_violations,
)
from instructions.ai_instruction_repository_format import (
    instruction_identity_violations,
)


def test_instruction_identity_ignores_frontmatter_serialization(tmp_path):
    skill_directory = tmp_path / "example-skill"
    skill_directory.mkdir()
    skill_file = skill_directory / "SKILL.md"
    skill_file.write_text(
        '---\nname: "example-skill"\ndescription: >\n  Routes one bounded operation.\n---\n'
        "### Scope\n\nprose\n"
    )
    assert instruction_identity_violations(skill_file) == []


@pytest.mark.parametrize(
    ("name", "description", "expected_rule"),
    [
        ("example_skill", "Routes one operation.", "instruction_name"),
        (
            "example-skill",
            "One. Two. Three.",
            "instruction_description",
        ),
        (
            "example-skill",
            " ".join(["word"] * 36),
            "instruction_description",
        ),
    ],
)
def test_instruction_identity_rejects_invalid_names_and_descriptions(
    tmp_path, name: str, description: str, expected_rule: str
):
    skill_directory = tmp_path / "example-skill"
    skill_directory.mkdir()
    skill_file = skill_directory / "SKILL.md"
    skill_file.write_text(
        f"---\nname: {name}\ndescription: {description}\n---\n### Scope\n\nprose\n"
    )
    actual_rules = {
        violation.rule for violation in instruction_identity_violations(skill_file)
    }
    assert expected_rule in actual_rules


def test_skill_reference_paths_reject_absolute_and_repository_root_forms(tmp_path):
    skill_file = tmp_path / "SKILL.md"
    skill_file.write_text(
        "### Routes\n\nRead `/tmp/example/references/testing.md` and "
        "`agent-harness/skills/example/references/testing.md`.\n"
    )
    assert noncanonical_skill_reference_paths(
        skill_file, inspect_markdown_instruction(skill_file.read_text())
    ) == [
        "/tmp/example/references/testing.md",
        "agent-harness/skills/example/references/testing.md",
    ]


def test_ai_instruction_files_follow_the_repository_format():
    violations = repository_instruction_format_violations()
    assert not violations, "AI instruction format violations:\n" + "\n".join(
        f"{path}: {message}"
        for path, messages in violations.items()
        for message in messages
    )
