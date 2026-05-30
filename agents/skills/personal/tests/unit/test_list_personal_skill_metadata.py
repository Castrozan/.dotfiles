import importlib.util
import json
from pathlib import Path


SCRIPT_PATH = (
    Path(__file__).resolve().parent.parent.parent
    / "scripts"
    / "list-personal-skill-metadata.py"
)
module_specification = importlib.util.spec_from_file_location(
    "list_personal_skill_metadata", SCRIPT_PATH
)
loaded_personal_skill_metadata_module = importlib.util.module_from_spec(
    module_specification
)
assert module_specification.loader is not None
module_specification.loader.exec_module(loaded_personal_skill_metadata_module)


def test_collect_personal_skill_metadata_returns_sorted_metadata_with_paths(tmp_path):
    personal_skill_vault_directory = tmp_path / "personal-skill-vault"

    browser_skill_directory = personal_skill_vault_directory / "browser"
    browser_skill_directory.mkdir(parents=True)
    (browser_skill_directory / "SKILL.md").write_text(
        "---\nname: browser\ndescription: Browser skill.\n---\n"
    )

    desktop_skill_directory = personal_skill_vault_directory / "desktop"
    desktop_skill_directory.mkdir()
    (desktop_skill_directory / "SKILL.md").write_text(
        "---\nname: desktop\ndescription: Desktop skill.\n---\n"
    )

    personal_skill_metadata = (
        loaded_personal_skill_metadata_module.collect_personal_skill_metadata(
            personal_skill_vault_directory
        )
    )

    assert personal_skill_metadata == [
        {
            "description": "Browser skill.",
            "directory_name": "browser",
            "name": "browser",
            "path": str(browser_skill_directory.resolve()),
            "skill_markdown_path": str(
                (browser_skill_directory / "SKILL.md").resolve()
            ),
            "chapters": [],
        },
        {
            "description": "Desktop skill.",
            "directory_name": "desktop",
            "name": "desktop",
            "path": str(desktop_skill_directory.resolve()),
            "skill_markdown_path": str(
                (desktop_skill_directory / "SKILL.md").resolve()
            ),
            "chapters": [],
        },
    ]


def test_collect_personal_skill_metadata_skips_directories_without_skill_markdown(
    tmp_path,
):
    personal_skill_vault_directory = tmp_path / "personal-skill-vault"
    (personal_skill_vault_directory / "missing").mkdir(parents=True)

    assert (
        loaded_personal_skill_metadata_module.collect_personal_skill_metadata(
            personal_skill_vault_directory
        )
        == []
    )


def test_collect_personal_skill_metadata_includes_umbrella_chapters(tmp_path):
    personal_skill_vault_directory = tmp_path / "personal-skill-vault"
    umbrella_skill_directory = personal_skill_vault_directory / "personal"
    umbrella_skill_directory.mkdir(parents=True)
    (umbrella_skill_directory / "SKILL.md").write_text(
        "---\nname: personal\ndescription: Master index.\n---\n"
    )
    (umbrella_skill_directory / "obsidian.md").write_text(
        "<vault_location>\n"
        "Vault path is at $OBSIDIAN_HOME with daily notes inside.\n"
        "</vault_location>\n"
    )
    (umbrella_skill_directory / "ponto.md").write_text(
        "Senior Gestao de Ponto - time entry automation via Chrome DevTools MCP.\n"
    )

    personal_skill_metadata = (
        loaded_personal_skill_metadata_module.collect_personal_skill_metadata(
            personal_skill_vault_directory
        )
    )

    assert len(personal_skill_metadata) == 1
    umbrella_metadata = personal_skill_metadata[0]
    assert umbrella_metadata["name"] == "personal"
    chapter_entries = umbrella_metadata["chapters"]
    assert len(chapter_entries) == 2
    obsidian_chapter, ponto_chapter = chapter_entries
    assert obsidian_chapter["name"] == "personal/obsidian"
    assert obsidian_chapter["path"] == str(
        (umbrella_skill_directory / "obsidian.md").resolve()
    )
    assert "Vault path is at $OBSIDIAN_HOME" in obsidian_chapter["preview"]
    assert "<vault_location>" not in obsidian_chapter["preview"]
    assert ponto_chapter["name"] == "personal/ponto"
    assert ponto_chapter["preview"].startswith("Senior Gestao de Ponto")


def test_extract_chapter_preview_truncates_long_text():
    very_long_chapter_content = "Sentence number one. " * 200
    chapter_preview = loaded_personal_skill_metadata_module.extract_chapter_preview(
        very_long_chapter_content
    )
    assert chapter_preview.endswith("...")
    assert (
        len(chapter_preview)
        <= loaded_personal_skill_metadata_module.CHAPTER_PREVIEW_MAXIMUM_CHARACTER_COUNT
        + len("...")
    )


def test_render_personal_skill_metadata_json_uses_expected_shape(tmp_path):
    personal_skill_vault_directory = tmp_path / "personal-skill-vault"
    browser_skill_directory = personal_skill_vault_directory / "browser"
    browser_skill_directory.mkdir(parents=True)
    (browser_skill_directory / "SKILL.md").write_text(
        "---\nname: browser\ndescription: Browser skill.\n---\n"
    )

    rendered_metadata = (
        loaded_personal_skill_metadata_module.render_personal_skill_metadata_json(
            personal_skill_vault_directory
        )
    )
    parsed_metadata = json.loads(rendered_metadata)

    assert parsed_metadata == {
        "personal_skill_vault_directory": str(personal_skill_vault_directory.resolve()),
        "skills": [
            {
                "description": "Browser skill.",
                "directory_name": "browser",
                "name": "browser",
                "path": str(browser_skill_directory.resolve()),
                "skill_markdown_path": str(
                    (browser_skill_directory / "SKILL.md").resolve()
                ),
                "chapters": [],
            }
        ],
    }
