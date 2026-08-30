import pytest

from ai_instruction_format import (
    MAXIMUM_INSTRUCTION_PROSE_LINES,
    MAXIMUM_XML_SECTION_PROSE_LINES,
    instruction_format_violations,
)
from ai_instruction_references import noncanonical_skill_reference_paths
from ai_instruction_repository_format import repository_instruction_format_violations
from ai_instruction_repository_format import instruction_identity_violations


def prose_lines(count: int) -> str:
    return "\n".join(f"prose line {number}" for number in range(count))


@pytest.mark.parametrize(
    ("text", "expected_rules"),
    [
        (
            "---\nname: example\ndescription: Example.\n---\n"
            "<one_section>\nprose\n</one_section>\n",
            set(),
        ),
        (
            "---\n" + prose_lines(40) + "\n---\n<one_section>\nprose\n</one_section>\n",
            set(),
        ),
        (
            "<one_section>\n\nprose\n</one_section>\n",
            {"blank_line_inside_xml_section"},
        ),
        (
            "<one_section>\n" + prose_lines(21) + "\n</one_section>\n",
            {"xml_section_prose_line_limit"},
        ),
        (
            "<one_section>\n"
            + prose_lines(MAXIMUM_INSTRUCTION_PROSE_LINES + 1)
            + "\n</one_section>\n",
            {"instruction_prose_line_limit", "xml_section_prose_line_limit"},
        ),
        (
            "<hyphenated-tag>\nprose\n</hyphenated-tag>\n"
            "<Uppercase>\nprose\n</Uppercase>\n",
            {"xml_tag_name"},
        ),
        (
            "<outer>\n<inner>\nprose\n</inner>\n</outer>\n",
            {"nested_xml_section"},
        ),
        (
            "prose\n<one_section>\nmore prose\n</one_section>\n",
            {"prose_outside_xml_section"},
        ),
        (
            "<one_section>\nprose\n</different_section>\n",
            {"xml_tag_balance"},
        ),
    ],
)
def test_instruction_format_validator_has_focused_rule_coverage(
    text: str, expected_rules: set[str]
):
    actual_rules = {violation.rule for violation in instruction_format_violations(text)}
    assert actual_rules == expected_rules


def test_the_section_limit_is_stricter_than_the_file_limit():
    assert MAXIMUM_XML_SECTION_PROSE_LINES == 20
    assert MAXIMUM_INSTRUCTION_PROSE_LINES == 150


def test_instruction_identity_ignores_frontmatter_serialization(tmp_path):
    skill_directory = tmp_path / "example-skill"
    skill_directory.mkdir()
    skill_file = skill_directory / "SKILL.md"
    skill_file.write_text(
        '---\nname: "example-skill"\ndescription: >\n  Routes one bounded operation.\n---\n'
        "<scope>\nprose\n</scope>\n"
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
        f"---\nname: {name}\ndescription: {description}\n---\n"
        "<scope>\nprose\n</scope>\n"
    )
    actual_rules = {
        violation.rule for violation in instruction_identity_violations(skill_file)
    }
    assert expected_rule in actual_rules


def test_skill_reference_paths_reject_absolute_and_repository_root_forms(tmp_path):
    skill_file = tmp_path / "SKILL.md"
    skill_file.write_text(
        "<routes>\nRead `/tmp/example/references/testing.md` and "
        "`agent-harness/skills/example/references/testing.md`.\n</routes>\n"
    )
    assert noncanonical_skill_reference_paths(skill_file) == [
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
