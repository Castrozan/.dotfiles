#!/usr/bin/env python3

import argparse
import json
import re
from pathlib import Path

CHAPTER_PREVIEW_MAXIMUM_CHARACTER_COUNT = 240


def parse_skill_markdown_frontmatter(skill_markdown_content: str) -> dict[str, str]:
    if not skill_markdown_content.startswith("---\n"):
        return {}
    frontmatter_parts = skill_markdown_content.split("---", 2)
    if len(frontmatter_parts) < 3:
        return {}
    parsed_frontmatter: dict[str, str] = {}
    for frontmatter_line in frontmatter_parts[1].splitlines():
        if ":" not in frontmatter_line:
            continue
        field_name, field_value = frontmatter_line.split(":", 1)
        parsed_frontmatter[field_name.strip()] = field_value.strip()
    return parsed_frontmatter


def strip_xml_like_tags(raw_text: str) -> str:
    return re.sub(r"<[^>]+>", " ", raw_text)


def collapse_whitespace(raw_text: str) -> str:
    return re.sub(r"\s+", " ", raw_text).strip()


def extract_chapter_preview(chapter_markdown_content: str) -> str:
    cleaned_chapter_text = collapse_whitespace(
        strip_xml_like_tags(chapter_markdown_content)
    )
    if len(cleaned_chapter_text) <= CHAPTER_PREVIEW_MAXIMUM_CHARACTER_COUNT:
        return cleaned_chapter_text
    return (
        cleaned_chapter_text[:CHAPTER_PREVIEW_MAXIMUM_CHARACTER_COUNT].rstrip() + "..."
    )


def collect_umbrella_chapter_metadata(
    umbrella_skill_directory: Path,
) -> list[dict[str, str]]:
    collected_umbrella_chapter_metadata: list[dict[str, str]] = []
    for chapter_markdown_path in sorted(umbrella_skill_directory.glob("*.md")):
        if chapter_markdown_path.name == "SKILL.md":
            continue
        chapter_preview = extract_chapter_preview(chapter_markdown_path.read_text())
        collected_umbrella_chapter_metadata.append(
            {
                "name": f"{umbrella_skill_directory.name}/{chapter_markdown_path.stem}",
                "path": str(chapter_markdown_path.resolve()),
                "preview": chapter_preview,
            }
        )
    nested_skills_directory = umbrella_skill_directory / "skills"
    if nested_skills_directory.is_dir():
        for nested_skill_directory in sorted(nested_skills_directory.iterdir()):
            nested_skill_markdown_path = nested_skill_directory / "SKILL.md"
            if not nested_skill_markdown_path.is_file():
                continue
            chapter_preview = extract_chapter_preview(
                nested_skill_markdown_path.read_text()
            )
            collected_umbrella_chapter_metadata.append(
                {
                    "name": f"{umbrella_skill_directory.name}/{nested_skill_directory.name}",
                    "path": str(nested_skill_markdown_path.resolve()),
                    "preview": chapter_preview,
                }
            )
    return collected_umbrella_chapter_metadata


def collect_personal_skill_metadata(
    personal_skill_vault_directory: Path,
) -> list[dict[str, object]]:
    resolved_personal_skill_vault_directory = personal_skill_vault_directory.resolve()
    if not resolved_personal_skill_vault_directory.is_dir():
        return []

    collected_personal_skill_metadata: list[dict[str, object]] = []
    for personal_skill_directory in sorted(
        resolved_personal_skill_vault_directory.iterdir(),
        key=lambda personal_skill_directory: personal_skill_directory.name,
    ):
        personal_skill_markdown_path = personal_skill_directory / "SKILL.md"
        if not personal_skill_markdown_path.is_file():
            continue
        parsed_frontmatter = parse_skill_markdown_frontmatter(
            personal_skill_markdown_path.read_text()
        )
        umbrella_chapters = collect_umbrella_chapter_metadata(personal_skill_directory)
        collected_personal_skill_metadata.append(
            {
                "description": parsed_frontmatter.get("description", ""),
                "directory_name": personal_skill_directory.name,
                "name": parsed_frontmatter.get("name", personal_skill_directory.name),
                "path": str(personal_skill_directory.resolve()),
                "skill_markdown_path": str(personal_skill_markdown_path.resolve()),
                "chapters": umbrella_chapters,
            }
        )
    return collected_personal_skill_metadata


def render_personal_skill_metadata_json(
    personal_skill_vault_directory: Path,
) -> str:
    resolved_personal_skill_vault_directory = personal_skill_vault_directory.resolve()
    return json.dumps(
        {
            "personal_skill_vault_directory": str(
                resolved_personal_skill_vault_directory
            ),
            "skills": collect_personal_skill_metadata(
                resolved_personal_skill_vault_directory
            ),
        },
        indent=2,
    )


def build_argument_parser() -> argparse.ArgumentParser:
    argument_parser = argparse.ArgumentParser()
    argument_parser.add_argument(
        "personal_skill_vault_directory",
        nargs="?",
        default=Path.home()
        / ".local"
        / "share"
        / "claude-skill-sets"
        / "personal"
        / ".claude"
        / "skills",
        type=Path,
    )
    return argument_parser


def main() -> int:
    parsed_arguments = build_argument_parser().parse_args()
    print(
        render_personal_skill_metadata_json(
            parsed_arguments.personal_skill_vault_directory
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
