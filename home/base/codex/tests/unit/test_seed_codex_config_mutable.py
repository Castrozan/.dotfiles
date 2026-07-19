import stat

from seed_codex_config_test_support import read_live_config, run_seed


def test_seed_creates_mutable_config_from_nix_source(tmp_path):
    codex_directory = tmp_path / ".codex"
    codex_directory.mkdir()
    (codex_directory / "config.toml.nix-source").write_text(
        'model = "current-model"\n', encoding="utf-8"
    )

    result = run_seed(tmp_path)

    assert result.returncode == 0, result.stderr
    assert read_live_config(tmp_path)["model"] == "current-model"
    assert stat.S_IMODE((codex_directory / "config.toml").stat().st_mode) == 0o600


def test_seed_preserves_runtime_sections_and_replaces_source_owned_settings(
    tmp_path,
):
    codex_directory = tmp_path / ".codex"
    codex_directory.mkdir()
    (codex_directory / "config.toml.nix-source").write_text(
        """
model = "current-model"

[mcp_servers.current]
command = "current"

[projects."/declared-project"]
trust_level = "trusted"
""".strip()
        + "\n",
        encoding="utf-8",
    )
    (codex_directory / "config.toml").write_text(
        """
model = "stale-model"

[mcp_servers.stale]
command = "stale"

[projects."/runtime-project"]
trust_level = "trusted"

[projects."/declared-project"]
trust_level = "untrusted"

[marketplaces.community]
source = "https://example.invalid/marketplace.json"

[plugins."example@community"]
enabled = true
""".strip()
        + "\n",
        encoding="utf-8",
    )

    result = run_seed(tmp_path)

    assert result.returncode == 0, result.stderr
    live_config = read_live_config(tmp_path)
    assert live_config["model"] == "current-model"
    assert set(live_config["mcp_servers"]) == {"current"}
    assert set(live_config["projects"]) == {
        "/declared-project",
        "/runtime-project",
    }
    assert live_config["projects"]["/declared-project"] == {"trust_level": "trusted"}
    assert set(live_config["marketplaces"]) == {"community"}
    assert set(live_config["plugins"]) == {"example@community"}


def test_seed_removes_legacy_generated_profiles(tmp_path):
    codex_directory = tmp_path / ".codex"
    codex_directory.mkdir()
    (codex_directory / "config.toml.nix-source").write_text(
        'model = "current-model"\n', encoding="utf-8"
    )
    for profile_name in ("fast", "deep", "web"):
        (codex_directory / f"{profile_name}.config.toml").write_text(
            'model = "stale"\n', encoding="utf-8"
        )

    result = run_seed(tmp_path)

    assert result.returncode == 0, result.stderr
    assert not list(codex_directory.glob("*.config.toml"))


def test_seed_is_noop_without_nix_source(tmp_path):
    codex_directory = tmp_path / ".codex"
    codex_directory.mkdir()
    live_config_path = codex_directory / "config.toml"
    live_config_path.write_text('model = "keep-me"\n', encoding="utf-8")

    result = run_seed(tmp_path)

    assert result.returncode == 0, result.stderr
    assert live_config_path.read_text(encoding="utf-8") == 'model = "keep-me"\n'
