import json
import re
from pathlib import Path


PLUGIN_SCHEMA = "https://agent-plugins.org/schemas/1.0.0/plugin.schema.json"
SUPPORTED_TARGETS = frozenset({"claude", "codex", "opencode", "pi"})
NATIVE_COMPONENTS = frozenset(
    {
        "AGENTS.md",
        "CLAUDE.md",
        "SOUL.md",
        "agents",
        "commands",
        "hooks",
        "workflows",
        "rules",
        ".claude-plugin",
        ".codex-plugin",
        ".agents",
        ".claude",
        ".codex",
        ".opencode",
        ".pi",
        ".hermes",
        ".mcp.json",
        ".lsp.json",
        ".app.json",
    }
)


def read_portable_plugin(source: Path, targets: tuple[str, ...]) -> str:
    unsupported_targets = set(targets) - SUPPORTED_TARGETS
    if unsupported_targets or not targets:
        raise ValueError(f"Unsupported targets: {sorted(unsupported_targets)}")
    manifest = json.loads((source / "plugin.json").read_text())
    if not isinstance(manifest, dict) or manifest.get("$schema") != PLUGIN_SCHEMA:
        raise ValueError("Expected an Agent Plugins v1 plugin.json")
    name = manifest.get("name", "")
    if not isinstance(name, str) or not re.fullmatch(
        r"(?!.*(?:--|\.\.))[a-z0-9](?:[a-z0-9.-]{0,62}[a-z0-9])?", name
    ):
        raise ValueError("Invalid portable plugin name")
    native_components = any(
        child.name in NATIVE_COMPONENTS
        or (child.is_dir() and re.fullmatch(r"(?:[a-z0-9-]+\.)+[a-z0-9-]+", child.name))
        for child in source.iterdir()
    )
    if manifest.get("extensions") or native_components:
        raise ValueError(
            "Native extensions, instructions, hooks, agents and workflows "
            "need explicit adapters; this prototype only builds skills and MCP"
        )
    validate_portable_links(source)
    mcp_path = source / "mcp.json"
    if mcp_path.exists():
        validate_mcp_targets(mcp_path, targets)
    return name


def validate_portable_links(source: Path) -> None:
    for path in source.rglob("*"):
        if ".git" in path.relative_to(source).parts:
            continue
        if path.is_symlink():
            resolved = path.resolve(strict=True)
            if resolved.is_dir() or not resolved.is_relative_to(source):
                raise ValueError(f"Materialize directory or external symlinks: {path}")


def validate_mcp_targets(mcp_path: Path, targets: tuple[str, ...]) -> None:
    configuration = json.loads(mcp_path.read_text())
    if not isinstance(configuration, dict):
        raise ValueError("Expected an MCP configuration object")
    servers = configuration.get("mcpServers", {})
    if servers and "pi" in targets:
        raise ValueError("Pi projection supports skills only; MCP would be dropped")
    if "opencode" in targets and "${PLUGIN_DATA}" in mcp_path.read_text():
        raise ValueError(
            "OpenCode plugin data needs a writable runtime directory; "
            "this prototype only builds stateless MCP configurations"
        )
