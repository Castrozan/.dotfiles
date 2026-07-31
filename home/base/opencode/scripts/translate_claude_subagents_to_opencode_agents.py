#!/usr/bin/env python3

import json
import os
import sys
from pathlib import Path

FRONTMATTER_DELIMITER = "---"

CLAUDE_TOOL_NAME_TO_OPENCODE_PERMISSION_KEY = {
    "read": "read",
    "edit": "edit",
    "write": "edit",
    "notebookedit": "edit",
    "grep": "grep",
    "glob": "glob",
    "bash": "bash",
    "task": "task",
    "todowrite": "todowrite",
    "todoread": "todowrite",
    "webfetch": "webfetch",
    "websearch": "websearch",
    "skill": "skill",
}

ALWAYS_PERMITTED_OPENCODE_TOOLS = ("skill", "todowrite", "question")


def split_frontmatter_from_body(markdown_source):
    lines = markdown_source.splitlines()
    if not lines or lines[0].strip() != FRONTMATTER_DELIMITER:
        return {}, markdown_source
    closing_index = next(
        (
            index
            for index, line in enumerate(lines[1:], start=1)
            if line.strip() == FRONTMATTER_DELIMITER
        ),
        None,
    )
    if closing_index is None:
        return {}, markdown_source
    return (
        parse_frontmatter_fields(lines[1:closing_index]),
        "\n".join(lines[closing_index + 1 :]).lstrip("\n"),
    )


def parse_frontmatter_fields(frontmatter_lines):
    fields = {}
    current_field_name = None
    for line in frontmatter_lines:
        if line.startswith((" ", "\t")) and current_field_name:
            fields[current_field_name] = f"{fields[current_field_name]} {line.strip()}"
            continue
        field_name, separator, field_value = line.partition(":")
        if not separator:
            continue
        current_field_name = field_name.strip()
        fields[current_field_name] = field_value.strip()
    return fields


def parse_comma_separated_tool_names(raw_frontmatter_value):
    return [
        tool_name.strip()
        for tool_name in raw_frontmatter_value.split(",")
        if tool_name.strip()
    ]


def translate_tool_names_to_permission_keys(claude_tool_names):
    permission_keys = []
    for claude_tool_name in claude_tool_names:
        permission_key = CLAUDE_TOOL_NAME_TO_OPENCODE_PERMISSION_KEY.get(
            claude_tool_name.lower()
        )
        if permission_key and permission_key not in permission_keys:
            permission_keys.append(permission_key)
    return permission_keys


def build_permission_map(frontmatter_fields):
    allowed_tool_names = parse_comma_separated_tool_names(
        frontmatter_fields.get("tools", "")
    )
    disallowed_tool_names = parse_comma_separated_tool_names(
        frontmatter_fields.get("disallowedTools", "")
    )

    if allowed_tool_names and allowed_tool_names != ["*"]:
        permission_map = {"*": "deny"}
        for permission_key in translate_tool_names_to_permission_keys(
            allowed_tool_names
        ):
            permission_map[permission_key] = "allow"
        for permission_key in ALWAYS_PERMITTED_OPENCODE_TOOLS:
            permission_map.setdefault(permission_key, "allow")
        return permission_map

    permission_map = {"*": "allow"}
    for permission_key in translate_tool_names_to_permission_keys(
        disallowed_tool_names
    ):
        permission_map[permission_key] = "deny"
    return permission_map


def render_frontmatter_value(value):
    return json.dumps(value)


def translate_subagent_definition(markdown_source):
    frontmatter_fields, body = split_frontmatter_from_body(markdown_source)
    opencode_frontmatter = {
        "description": frontmatter_fields.get("description", ""),
        "mode": "subagent",
        "permission": build_permission_map(frontmatter_fields),
    }
    rendered_fields = "\n".join(
        f"{field_name}: {render_frontmatter_value(field_value)}"
        for field_name, field_value in opencode_frontmatter.items()
    )
    return (
        f"{FRONTMATTER_DELIMITER}\n{rendered_fields}\n{FRONTMATTER_DELIMITER}\n\n{body}"
    )


def translate_subagent_definition_directory(source_directory, destination_directory):
    destination_directory.mkdir(parents=True, exist_ok=True)
    for source_path in sorted(source_directory.glob("*.md")):
        translated = translate_subagent_definition(
            source_path.read_text(encoding="utf-8")
        )
        (destination_directory / source_path.name).write_text(
            translated, encoding="utf-8"
        )


def main():
    source_directory = Path(os.environ["CLAUDE_SUBAGENT_DEFINITIONS_DIRECTORY"])
    destination_directory = Path(os.environ["OPENCODE_AGENT_DEFINITIONS_DIRECTORY"])
    translate_subagent_definition_directory(source_directory, destination_directory)
    return 0


if __name__ == "__main__":
    sys.exit(main())
