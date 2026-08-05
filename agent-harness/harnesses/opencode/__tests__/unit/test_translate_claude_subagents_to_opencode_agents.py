import json

from translate_claude_subagents_to_opencode_agents import (
    build_permission_map,
    split_frontmatter_from_body,
    translate_subagent_definition,
    translate_subagent_definition_directory,
)

ALLOW_LIST_SUBAGENT = """---
name: software-engineer
description: Writes the code for a design that is already decided.
tools: Read, Edit, Write, Grep, Glob, Bash
model: sonnet
skills: coding
---

<job>
Implement the plan you were given.
</job>
"""

DENY_LIST_SUBAGENT = """---
name: Explore
description: Read-only codebase search.
disallowedTools: Write, Edit, NotebookEdit
model: haiku
---

<job>
Search and report.
</job>
"""


def test_split_frontmatter_from_body_separates_fields_and_body():
    fields, body = split_frontmatter_from_body(DENY_LIST_SUBAGENT)

    assert fields["name"] == "Explore"
    assert fields["disallowedTools"] == "Write, Edit, NotebookEdit"
    assert body.startswith("<job>")


def test_split_frontmatter_from_body_joins_wrapped_continuation_lines():
    fields, _ = split_frontmatter_from_body(
        "---\ndescription: first part\n  second part\n---\nbody\n"
    )

    assert fields["description"] == "first part second part"


def test_split_frontmatter_from_body_returns_whole_source_when_absent():
    fields, body = split_frontmatter_from_body("no frontmatter here\n")

    assert fields == {}
    assert body == "no frontmatter here\n"


def test_build_permission_map_turns_a_tool_allow_list_into_a_deny_by_default_map():
    fields, _ = split_frontmatter_from_body(ALLOW_LIST_SUBAGENT)

    permission_map = build_permission_map(fields)

    assert permission_map["*"] == "deny"
    assert permission_map["read"] == "allow"
    assert permission_map["edit"] == "allow"
    assert permission_map["bash"] == "allow"
    assert permission_map["skill"] == "allow"
    assert "websearch" not in permission_map


def test_build_permission_map_turns_a_disallowed_tool_list_into_an_allow_by_default_map():
    fields, _ = split_frontmatter_from_body(DENY_LIST_SUBAGENT)

    permission_map = build_permission_map(fields)

    assert permission_map["*"] == "allow"
    assert permission_map["edit"] == "deny"


def test_build_permission_map_defaults_to_full_access_without_tool_fields():
    assert build_permission_map({}) == {"*": "allow"}


def test_translate_subagent_definition_emits_opencode_frontmatter_and_keeps_the_body():
    translated = translate_subagent_definition(ALLOW_LIST_SUBAGENT)

    header, frontmatter, body = translated.split("---\n", 2)
    frontmatter_fields = dict(
        line.split(": ", 1) for line in frontmatter.strip().splitlines()
    )

    assert header == ""
    assert json.loads(frontmatter_fields["mode"]) == "subagent"
    assert json.loads(frontmatter_fields["description"]).startswith("Writes the code")
    assert json.loads(frontmatter_fields["permission"])["*"] == "deny"
    assert "model" not in frontmatter_fields
    assert "skills" not in frontmatter_fields
    assert body.strip().startswith("<job>")


def test_translate_subagent_definition_directory_writes_one_file_per_source(tmp_path):
    source_directory = tmp_path / "subagents"
    source_directory.mkdir()
    (source_directory / "software-engineer.md").write_text(ALLOW_LIST_SUBAGENT)
    (source_directory / "explore.md").write_text(DENY_LIST_SUBAGENT)
    destination_directory = tmp_path / "agent"

    translate_subagent_definition_directory(source_directory, destination_directory)

    assert sorted(path.name for path in destination_directory.glob("*.md")) == [
        "explore.md",
        "software-engineer.md",
    ]
    assert 'mode: "subagent"' in (destination_directory / "explore.md").read_text()
