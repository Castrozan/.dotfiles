import json
import os
from typing import Any


def read_pruned_config_substrings_from_environment() -> tuple[str, ...]:
    return tuple(
        substring.casefold()
        for substring in json.loads(
            os.environ.get("CODEX_PRUNED_CONFIG_SUBSTRINGS_JSON", "[]")
        )
        if isinstance(substring, str) and substring
    )


def config_value_matches_pruned_substring(
    value: Any, pruned_config_substrings: tuple[str, ...]
) -> bool:
    if isinstance(value, str):
        casefolded_value = value.casefold()
        return any(
            pruned_substring in casefolded_value
            for pruned_substring in pruned_config_substrings
        )
    if isinstance(value, dict):
        return any(
            config_value_matches_pruned_substring(key, pruned_config_substrings)
            or config_value_matches_pruned_substring(
                nested_value, pruned_config_substrings
            )
            for key, nested_value in value.items()
        )
    if isinstance(value, list):
        return any(
            config_value_matches_pruned_substring(item, pruned_config_substrings)
            for item in value
        )
    return False


def prune_private_matching_config_entries(
    config_data: dict[str, Any], pruned_config_substrings: tuple[str, ...]
) -> None:
    for config_section_name in ("projects", "mcp_servers", "plugins"):
        config_section = config_data.get(config_section_name)
        if not isinstance(config_section, dict):
            continue
        for config_entry_name in list(config_section):
            config_entry = {
                config_entry_name: config_section[config_entry_name],
            }
            if config_value_matches_pruned_substring(
                config_entry, pruned_config_substrings
            ):
                del config_section[config_entry_name]
