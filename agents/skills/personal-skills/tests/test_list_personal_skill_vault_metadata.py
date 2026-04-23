import importlib.util
import json
from pathlib import Path


SCRIPT_PATH = (
    Path(__file__).resolve().parent.parent
    / "scripts"
    / "list-personal-skill-vault-metadata.py"
)
module_specification = importlib.util.spec_from_file_location(
    "list_personal_skill_vault_metadata", SCRIPT_PATH
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
        },
        {
            "description": "Desktop skill.",
            "directory_name": "desktop",
            "name": "desktop",
            "path": str(desktop_skill_directory.resolve()),
            "skill_markdown_path": str(
                (desktop_skill_directory / "SKILL.md").resolve()
            ),
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
            }
        ],
    }
