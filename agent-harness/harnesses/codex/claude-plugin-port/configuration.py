import os
import pathlib
import shutil

PORTED_MARKETPLACE_NAME = "claude-code-ports"
PORTED_MARKETPLACE_DISPLAY_NAME = "Ported Claude Code plugins"
CODEX_COMMAND_TIMEOUT_SECONDS = 120

home_directory = pathlib.Path.home()
codex_home_directory = home_directory / ".codex"
codex_config_path = codex_home_directory / "config.toml"
ported_marketplace_root = codex_home_directory / "claude-plugin-ports"
ported_marketplace_manifest = (
    ported_marketplace_root / ".agents" / "plugins" / "marketplace.json"
)
ported_plugin_cache_root = (
    codex_home_directory / "plugins" / "cache" / PORTED_MARKETPLACE_NAME
)


def resolve_codex_binary():
    configured_codex_binary = os.environ.get("CODEX_BIN", "")
    if configured_codex_binary and pathlib.Path(configured_codex_binary).exists():
        return pathlib.Path(configured_codex_binary)
    discovered_codex_binary = shutil.which("codex")
    return pathlib.Path(discovered_codex_binary) if discovered_codex_binary else None
