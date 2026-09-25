import pytest

from seed_codex_config_test_support import read_live_config, run_seed


@pytest.mark.parametrize("enabled", [True, False])
def test_seed_merges_managed_server_policy_without_replacing_plugin_choices(
    tmp_path, enabled
):
    codex_directory = tmp_path / ".codex"
    codex_directory.mkdir()
    (codex_directory / "config.toml.nix-source").write_text(
        '[plugins."browser@community".mcp_servers.chrome]\nenabled = false\n',
        encoding="utf-8",
    )
    (codex_directory / "config.toml").write_text(
        f"""[plugins."browser@community"]
enabled = {str(enabled).lower()}

[plugins."browser@community".mcp_servers.chrome]
enabled = true
default_tools_approval_mode = "prompt"

[plugins."browser@community".mcp_servers.docs]
enabled = true

[plugins."another@community"]
enabled = true
""",
        encoding="utf-8",
    )

    result = run_seed(tmp_path)

    assert result.returncode == 0, result.stderr
    plugins = read_live_config(tmp_path)["plugins"]
    assert plugins["browser@community"] == {
        "enabled": enabled,
        "mcp_servers": {
            "chrome": {"enabled": False, "default_tools_approval_mode": "prompt"},
            "docs": {"enabled": True},
        },
    }
    assert plugins["another@community"] == {"enabled": True}
