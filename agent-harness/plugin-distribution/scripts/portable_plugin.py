import json
import re
from pathlib import Path


PLUGIN_SCHEMA = "https://agent-plugins.org/schemas/1.0.0/plugin.schema.json"
SUPPORTED_TARGETS = frozenset({"claude", "codex", "opencode", "pi", "hermes"})


def read_portable_plugin(source: Path, targets: tuple[str, ...]) -> str:
    unsupported_targets = set(targets) - SUPPORTED_TARGETS
    if unsupported_targets:
        raise ValueError(f"Unsupported targets: {sorted(unsupported_targets)}")
    manifest = json.loads((source / "plugin.json").read_text())
    if not isinstance(manifest, dict) or manifest.get("$schema") != PLUGIN_SCHEMA:
        raise ValueError("Expected an Agent Plugins v1 plugin.json")
    name = manifest.get("name", "")
    if not isinstance(name, str) or not re.fullmatch(
        r"(?!.*(?:--|\.\.))[a-z0-9](?:[a-z0-9.-]{0,62}[a-z0-9])?", name
    ):
        raise ValueError("Invalid portable plugin name")
    validate_portable_links(source)
    return name


def validate_portable_links(source: Path) -> None:
    for path in source.rglob("*"):
        if ".git" in path.relative_to(source).parts:
            continue
        if path.is_symlink():
            resolved = path.resolve(strict=True)
            if resolved.is_dir() or not resolved.is_relative_to(source):
                raise ValueError(f"Materialize directory or external symlinks: {path}")
