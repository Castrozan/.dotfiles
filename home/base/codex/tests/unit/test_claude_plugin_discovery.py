import json

import claude_plugin_discovery
from claude_plugin_discovery import (
    read_installed_third_party_plugins,
    resolve_component_directory,
    strip_relative_prefix,
)


def test_strip_relative_prefix_removes_only_leading_dot_slash():
    assert strip_relative_prefix("./.claude/skills") == ".claude/skills"
    assert strip_relative_prefix("./skills") == "skills"
    assert strip_relative_prefix("skills") == "skills"


def test_resolve_component_directory_prefers_manifest_value(tmp_path):
    manifest_directory = tmp_path / "declared"
    manifest_directory.mkdir()
    (manifest_directory / "SKILL.md").write_text("x")
    conventional_directory = tmp_path / "skills"
    conventional_directory.mkdir()
    (conventional_directory / "SKILL.md").write_text("x")

    resolved = resolve_component_directory(tmp_path, "./declared", ["./skills"])

    assert resolved == manifest_directory


def test_resolve_component_directory_falls_back_to_conventional_path(tmp_path):
    conventional_directory = tmp_path / ".claude" / "skills"
    conventional_directory.mkdir(parents=True)
    (conventional_directory / "SKILL.md").write_text("x")

    resolved = resolve_component_directory(
        tmp_path, None, ["./skills", "./.claude/skills"]
    )

    assert resolved == conventional_directory


def test_resolve_component_directory_ignores_empty_directory(tmp_path):
    (tmp_path / "skills").mkdir()

    assert resolve_component_directory(tmp_path, None, ["./skills"]) is None


def _write_installed_plugins(tmp_path, monkeypatch, plugins):
    manifest_path = tmp_path / "installed_plugins.json"
    manifest_path.write_text(json.dumps({"plugins": plugins}))
    monkeypatch.setattr(
        claude_plugin_discovery, "installed_plugins_manifest", manifest_path
    )


def test_read_installed_third_party_plugins_skips_official_and_invalid(
    tmp_path, monkeypatch
):
    third_party_install = tmp_path / "third-party"
    third_party_install.mkdir()
    official_install = tmp_path / "official"
    official_install.mkdir()

    _write_installed_plugins(
        tmp_path,
        monkeypatch,
        {
            "figma@claude-plugins-official": [{"installPath": str(official_install)}],
            "empty@team-marketplace": [],
            "no-path@team-marketplace": [{"version": "1.0.0"}],
            "missing-dir@team-marketplace": [{"installPath": str(tmp_path / "absent")}],
            "real@team-marketplace": [
                {"installPath": str(third_party_install), "gitCommitSha": "abc123"}
            ],
        },
    )

    discovered = read_installed_third_party_plugins()

    assert [plugin["name"] for plugin in discovered] == ["real"]
    assert discovered[0]["version_source"] == "abc123"
    assert discovered[0]["install_directory"] == third_party_install


def test_read_installed_third_party_plugins_version_source_precedence(
    tmp_path, monkeypatch
):
    install_with_version = tmp_path / "with-version"
    install_with_version.mkdir()
    install_without_either = tmp_path / "without-either"
    install_without_either.mkdir()

    _write_installed_plugins(
        tmp_path,
        monkeypatch,
        {
            "versioned@team": [
                {"installPath": str(install_with_version), "version": "9.9.9"}
            ],
            "bare@team": [{"installPath": str(install_without_either)}],
        },
    )

    discovered = {
        plugin["name"]: plugin["version_source"]
        for plugin in read_installed_third_party_plugins()
    }

    assert discovered["versioned"] == "9.9.9"
    assert discovered["bare"] == "unknown"


def test_read_installed_third_party_plugins_missing_manifest_returns_empty(
    tmp_path, monkeypatch
):
    monkeypatch.setattr(
        claude_plugin_discovery, "installed_plugins_manifest", tmp_path / "absent.json"
    )

    assert read_installed_third_party_plugins() == []


def test_read_installed_third_party_plugins_prunes_private_matching_names(
    tmp_path, monkeypatch
):
    private_install = tmp_path / "work-only"
    private_install.mkdir()
    personal_install = tmp_path / "personal"
    personal_install.mkdir()
    _write_installed_plugins(
        tmp_path,
        monkeypatch,
        {
            "work-only@team": [{"installPath": str(private_install)}],
            "personal@team": [{"installPath": str(personal_install)}],
        },
    )

    discovered = read_installed_third_party_plugins(("WORK-ONLY",))

    assert [plugin["name"] for plugin in discovered] == ["personal"]
