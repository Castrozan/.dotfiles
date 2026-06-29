import json
import re
import shutil

from configuration import (
    PORTED_MARKETPLACE_DISPLAY_NAME,
    PORTED_MARKETPLACE_NAME,
    ported_marketplace_manifest,
    ported_marketplace_root,
)


def sanitize_semver_build_metadata(value):
    cleaned = re.sub(r"[^0-9A-Za-z-]", "-", value)
    return cleaned or "unknown"


def build_ported_plugin(
    plugin_name, version_source, description, skills_directory, commands_directory
):
    plugin_root = ported_marketplace_root / "plugins" / plugin_name
    (plugin_root / ".codex-plugin").mkdir(parents=True, exist_ok=True)
    plugin_manifest = {
        "name": plugin_name,
        "version": f"0.0.0+{sanitize_semver_build_metadata(version_source)}",
        "description": description
        or f"Claude Code plugin {plugin_name} ported to Codex.",
    }
    if skills_directory is not None:
        shutil.copytree(
            skills_directory,
            plugin_root / "skills",
            symlinks=False,
            ignore_dangling_symlinks=True,
        )
        plugin_manifest["skills"] = "./skills/"
    if commands_directory is not None:
        shutil.copytree(
            commands_directory,
            plugin_root / "commands",
            symlinks=False,
            ignore_dangling_symlinks=True,
        )
    (plugin_root / ".codex-plugin" / "plugin.json").write_text(
        json.dumps(plugin_manifest, indent=2)
    )
    return {
        "name": plugin_name,
        "source": {"source": "local", "path": f"./plugins/{plugin_name}"},
        "policy": {"installation": "AVAILABLE", "authentication": "ON_USE"},
        "category": "Productivity",
    }


def write_marketplace_manifest(ported_marketplace_entries):
    ported_marketplace_manifest.write_text(
        json.dumps(
            {
                "name": PORTED_MARKETPLACE_NAME,
                "interface": {"displayName": PORTED_MARKETPLACE_DISPLAY_NAME},
                "plugins": ported_marketplace_entries,
            },
            indent=2,
        )
    )
