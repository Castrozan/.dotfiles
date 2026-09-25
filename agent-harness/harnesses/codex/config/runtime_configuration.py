runtime_preserved_value_names = ("model",)
runtime_preserved_section_names = ("projects", "marketplaces", "plugins")


def merge_runtime_preserved_configuration(
    nix_source: dict, current_config: dict
) -> dict:
    merged_config = dict(nix_source)
    for value_name in runtime_preserved_value_names:
        if value_name in current_config:
            merged_config[value_name] = current_config[value_name]
    for section_name in runtime_preserved_section_names:
        current_section = current_config.get(section_name)
        source_section = nix_source.get(section_name)
        if not isinstance(current_section, dict):
            continue
        if section_name == "plugins" and isinstance(source_section, dict):
            merged_config[section_name] = merge_plugin_policy(
                current_section, source_section
            )
        elif isinstance(source_section, dict):
            merged_config[section_name] = current_section | source_section
        elif section_name not in nix_source:
            merged_config[section_name] = current_section
    source_hooks = nix_source.get("hooks", {})
    current_hooks = current_config.get("hooks", {})
    if isinstance(source_hooks, dict) and isinstance(current_hooks, dict):
        current_hook_state = current_hooks.get("state")
        source_hook_state = source_hooks.get("state", {})
        if isinstance(current_hook_state, dict) and isinstance(source_hook_state, dict):
            merged_config["hooks"] = source_hooks | {
                "state": current_hook_state | source_hook_state
            }
    return merged_config


def merge_plugin_policy(current_policy: dict, source_policy: dict) -> dict:
    merged_policy = dict(current_policy)
    for name, source_value in source_policy.items():
        current_value = current_policy.get(name)
        merged_policy[name] = (
            merge_plugin_policy(current_value, source_value)
            if isinstance(current_value, dict) and isinstance(source_value, dict)
            else source_value
        )
    return merged_policy
