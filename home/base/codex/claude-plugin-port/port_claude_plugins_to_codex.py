import shutil

from claude_plugin_discovery import (
    read_claude_plugin_manifest,
    read_enabled_plugin_keys,
    read_installed_third_party_plugins,
    resolve_component_directory,
)
from codex_marketplace import build_ported_plugin, write_marketplace_manifest
from codex_plugin_cli import (
    ported_marketplace_is_registered,
    previously_ported_plugin_names,
    run_codex_plugin_command,
)
from configuration import (
    PORTED_MARKETPLACE_NAME,
    ported_marketplace_manifest,
    ported_marketplace_root,
)


def collect_ported_plugins():
    ported_marketplace_entries = []
    ported_plugin_names = []
    enabled_plugin_keys = read_enabled_plugin_keys()
    for third_party_plugin in read_installed_third_party_plugins(enabled_plugin_keys):
        install_directory = third_party_plugin["install_directory"]
        claude_plugin_manifest = read_claude_plugin_manifest(install_directory)
        skills_directory = resolve_component_directory(
            install_directory,
            claude_plugin_manifest.get("skills"),
            ["./skills", "./.claude/skills"],
        )
        commands_directory = resolve_component_directory(
            install_directory,
            claude_plugin_manifest.get("commands"),
            ["./commands", "./.claude/commands"],
        )
        if skills_directory is None and commands_directory is None:
            continue
        ported_marketplace_manifest.parent.mkdir(parents=True, exist_ok=True)
        ported_marketplace_entries.append(
            build_ported_plugin(
                third_party_plugin["name"],
                third_party_plugin["version_source"],
                claude_plugin_manifest.get("description", ""),
                skills_directory,
                commands_directory,
            )
        )
        ported_plugin_names.append(third_party_plugin["name"])
    return ported_marketplace_entries, ported_plugin_names


def remove_stale_ported_plugins(current_plugin_names):
    for stale_plugin_name in previously_ported_plugin_names() - set(
        current_plugin_names
    ):
        run_codex_plugin_command(
            ["remove", f"{stale_plugin_name}@{PORTED_MARKETPLACE_NAME}"]
        )


def register_ported_plugins(ported_plugin_names):
    marketplace_add_code, _, marketplace_add_error = run_codex_plugin_command(
        ["marketplace", "add", str(ported_marketplace_root)]
    )
    if marketplace_add_code != 0:
        print(
            f"codex-claude-plugin-port: marketplace add failed: {marketplace_add_error}"
        )
        return []
    installed_plugin_names = []
    for ported_plugin_name in ported_plugin_names:
        plugin_add_code, _, plugin_add_error = run_codex_plugin_command(
            ["add", f"{ported_plugin_name}@{PORTED_MARKETPLACE_NAME}"]
        )
        if plugin_add_code == 0:
            installed_plugin_names.append(ported_plugin_name)
        else:
            print(
                f"codex-claude-plugin-port: add {ported_plugin_name} failed: {plugin_add_error}"
            )
    return installed_plugin_names


def main():
    if ported_marketplace_root.exists():
        shutil.rmtree(ported_marketplace_root)

    ported_marketplace_entries, ported_plugin_names = collect_ported_plugins()
    remove_stale_ported_plugins(ported_plugin_names)

    if not ported_marketplace_entries:
        if ported_marketplace_is_registered():
            run_codex_plugin_command(["marketplace", "remove", PORTED_MARKETPLACE_NAME])
        print(
            "codex-claude-plugin-port: no enabled third-party Claude plugins with skills or commands to port"
        )
        return 0

    write_marketplace_manifest(ported_marketplace_entries)
    installed_plugin_names = register_ported_plugins(ported_plugin_names)
    print(
        "codex-claude-plugin-port: installed "
        f"{', '.join(installed_plugin_names) or 'nothing'} "
        f"into Codex marketplace {PORTED_MARKETPLACE_NAME}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
