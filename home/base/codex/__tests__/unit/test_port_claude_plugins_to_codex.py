import port_claude_plugins_to_codex


def test_remove_stale_ported_plugin_cache_keeps_only_current_plugins(
    tmp_path, monkeypatch
):
    cache_root = tmp_path / "claude-code-ports"
    current_plugin_cache = cache_root / "current-plugin" / "1.0.0"
    stale_plugin_cache = cache_root / "stale-plugin" / "1.0.0"
    current_plugin_cache.mkdir(parents=True)
    stale_plugin_cache.mkdir(parents=True)
    monkeypatch.setattr(
        port_claude_plugins_to_codex, "ported_plugin_cache_root", cache_root
    )

    port_claude_plugins_to_codex.remove_stale_ported_plugin_cache({"current-plugin"})

    assert current_plugin_cache.is_dir()
    assert not stale_plugin_cache.exists()


def test_remove_stale_ported_plugin_cache_removes_empty_marketplace_root(
    tmp_path, monkeypatch
):
    cache_root = tmp_path / "claude-code-ports"
    (cache_root / "stale-plugin" / "1.0.0").mkdir(parents=True)
    monkeypatch.setattr(
        port_claude_plugins_to_codex, "ported_plugin_cache_root", cache_root
    )

    port_claude_plugins_to_codex.remove_stale_ported_plugin_cache(set())

    assert not cache_root.exists()


def test_main_prunes_cache_when_claude_has_no_enabled_plugins(tmp_path, monkeypatch):
    cache_root = tmp_path / "plugins" / "cache" / "claude-code-ports"
    (cache_root / "stale-plugin" / "1.0.0").mkdir(parents=True)
    monkeypatch.setattr(
        port_claude_plugins_to_codex, "ported_plugin_cache_root", cache_root
    )
    monkeypatch.setattr(
        port_claude_plugins_to_codex,
        "ported_marketplace_root",
        tmp_path / "claude-plugin-ports",
    )
    monkeypatch.setattr(
        port_claude_plugins_to_codex, "collect_ported_plugins", lambda: ([], [])
    )
    monkeypatch.setattr(
        port_claude_plugins_to_codex, "remove_stale_ported_plugins", lambda names: None
    )
    monkeypatch.setattr(
        port_claude_plugins_to_codex,
        "ported_marketplace_is_registered",
        lambda: False,
    )

    result = port_claude_plugins_to_codex.main()

    assert result == 0
    assert not cache_root.exists()
