import json
import pathlib

from configuration import (
    OFFICIAL_MARKETPLACE_SUFFIX,
    installed_plugins_manifest,
)


def strip_relative_prefix(relative_path):
    return relative_path[2:] if relative_path.startswith("./") else relative_path


def read_installed_third_party_plugins(pruned_plugin_substrings=()):
    if not installed_plugins_manifest.exists():
        return []
    try:
        manifest = json.loads(installed_plugins_manifest.read_text())
    except json.JSONDecodeError:
        return []
    third_party_plugins = []
    for plugin_key, install_records in manifest.get("plugins", {}).items():
        if plugin_key.endswith(OFFICIAL_MARKETPLACE_SUFFIX):
            continue
        plugin_name = plugin_key.split("@", 1)[0]
        casefolded_plugin_name = plugin_name.casefold()
        if any(
            pruned_substring.casefold() in casefolded_plugin_name
            for pruned_substring in pruned_plugin_substrings
        ):
            continue
        if not install_records:
            continue
        install_record = install_records[0]
        install_path = install_record.get("installPath")
        if not install_path:
            continue
        install_directory = pathlib.Path(install_path)
        if not install_directory.is_dir():
            continue
        third_party_plugins.append(
            {
                "name": plugin_name,
                "install_directory": install_directory,
                "version_source": (
                    install_record.get("gitCommitSha")
                    or install_record.get("version")
                    or "unknown"
                ),
            }
        )
    return third_party_plugins


def read_claude_plugin_manifest(install_directory):
    manifest_path = install_directory / ".claude-plugin" / "plugin.json"
    if not manifest_path.exists():
        return {}
    try:
        return json.loads(manifest_path.read_text())
    except json.JSONDecodeError:
        return {}


def resolve_component_directory(
    install_directory, manifest_value, conventional_relative_paths
):
    candidate_relative_paths = []
    if isinstance(manifest_value, str):
        candidate_relative_paths.append(manifest_value)
    candidate_relative_paths.extend(conventional_relative_paths)
    for relative_path in candidate_relative_paths:
        candidate_directory = install_directory / strip_relative_prefix(relative_path)
        if candidate_directory.is_dir() and any(candidate_directory.iterdir()):
            return candidate_directory
    return None
