import json

import codex_marketplace
from codex_marketplace import build_ported_plugin, sanitize_semver_build_metadata


def test_sanitize_semver_build_metadata_keeps_hex_sha():
    assert (
        sanitize_semver_build_metadata("cd661e48079661f57dc8") == "cd661e48079661f57dc8"
    )


def test_sanitize_semver_build_metadata_replaces_invalid_characters():
    assert sanitize_semver_build_metadata("1.0_beta/2") == "1-0-beta-2"


def test_sanitize_semver_build_metadata_empty_becomes_unknown():
    assert sanitize_semver_build_metadata("") == "unknown"


def _stub_marketplace_root(tmp_path, monkeypatch):
    monkeypatch.setattr(codex_marketplace, "ported_marketplace_root", tmp_path)


def test_build_ported_plugin_copies_skills_and_commands(tmp_path, monkeypatch):
    source = tmp_path / "source"
    skills_directory = source / "skills"
    skills_directory.mkdir(parents=True)
    (skills_directory / "SKILL.md").write_text("skill")
    commands_directory = source / "commands"
    commands_directory.mkdir(parents=True)
    (commands_directory / "do-it.md").write_text("command")
    _stub_marketplace_root(tmp_path / "ported", monkeypatch)

    entry = build_ported_plugin(
        "example", "abc123", "Ported description", skills_directory, commands_directory
    )

    plugin_root = tmp_path / "ported" / "plugins" / "example"
    manifest = json.loads((plugin_root / ".codex-plugin" / "plugin.json").read_text())
    assert manifest["name"] == "example"
    assert manifest["version"] == "0.0.0+abc123"
    assert manifest["description"] == "Ported description"
    assert manifest["skills"] == "./skills/"
    assert (plugin_root / "skills" / "SKILL.md").read_text() == "skill"
    assert (plugin_root / "commands" / "do-it.md").read_text() == "command"
    assert entry["source"] == {"source": "local", "path": "./plugins/example"}
    assert entry["policy"] == {"installation": "AVAILABLE", "authentication": "ON_USE"}


def test_build_ported_plugin_skills_only_omits_commands_and_skills_field(
    tmp_path, monkeypatch
):
    skills_directory = tmp_path / "source" / "skills"
    skills_directory.mkdir(parents=True)
    (skills_directory / "SKILL.md").write_text("skill")
    _stub_marketplace_root(tmp_path / "ported", monkeypatch)

    build_ported_plugin("example", "abc", "", skills_directory, None)

    plugin_root = tmp_path / "ported" / "plugins" / "example"
    manifest = json.loads((plugin_root / ".codex-plugin" / "plugin.json").read_text())
    assert "skills" in manifest
    assert not (plugin_root / "commands").exists()
    assert manifest["description"] == "Claude Code plugin example ported to Codex."
