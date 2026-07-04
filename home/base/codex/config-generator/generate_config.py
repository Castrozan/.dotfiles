import json
import os
import pathlib
import tomllib
from typing import Any

from toml_render import render_codex_config_toml

codex_default_model = os.environ.get("CODEX_DEFAULT_MODEL", "gpt-5.5")
codex_developer_instructions = os.environ.get(
    "CODEX_DEVELOPER_INSTRUCTIONS",
    (
        "Operate pragmatically: keep diffs small, verify with fast checks, and "
        "prefer repo-local truth (AGENTS.md, bin/, home/{base,linux,darwin}/). Use profiles: "
        "fast (default), deep, web."
    ),
)
chrome_devtools_mcp_command = os.environ["CODEX_CHROME_DEVTOOLS_MCP_COMMAND"]
chrome_devtools_mcp_args = json.loads(os.environ["CODEX_CHROME_DEVTOOLS_MCP_ARGS_JSON"])
brave_devtools_mcp_command = os.environ["CODEX_BRAVE_DEVTOOLS_MCP_COMMAND"]
brave_devtools_mcp_args = json.loads(os.environ["CODEX_BRAVE_DEVTOOLS_MCP_ARGS_JSON"])


def build_trusted_project_entries() -> dict[str, dict[str, str]]:
    home_directory = pathlib.Path.home()
    trusted_project_entries = {
        str(home_directory): {"trust_level": "trusted"},
        str(home_directory / ".dotfiles"): {"trust_level": "trusted"},
    }

    extra_trusted_parents_env = os.environ.get(
        "CODEX_EXTRA_TRUSTED_PARENT_DIRECTORIES", ""
    )
    extra_trusted_parents = [
        pathlib.Path(os.path.expanduser(entry.strip()))
        for entry in extra_trusted_parents_env.split(":")
        if entry.strip()
    ]

    for trusted_parent_directory in [
        home_directory / "repo",
        *extra_trusted_parents,
    ]:
        if not trusted_parent_directory.is_dir():
            continue

        for trusted_child_directory in sorted(trusted_parent_directory.iterdir()):
            if trusted_child_directory.is_dir():
                trusted_project_entries[str(trusted_child_directory)] = {
                    "trust_level": "trusted"
                }

    return trusted_project_entries


def build_mcp_server_entries() -> dict[str, dict[str, Any]]:
    return {
        "chrome-devtools": {
            "command": chrome_devtools_mcp_command,
            "args": chrome_devtools_mcp_args,
        },
        "brave-devtools": {
            "command": brave_devtools_mcp_command,
            "args": brave_devtools_mcp_args,
        },
    }


PROFILE_OVERRIDES = {
    "fast": {
        "model": codex_default_model,
        "model_reasoning_effort": "xhigh",
        "model_reasoning_summary": "none",
        "model_verbosity": "low",
    },
    "deep": {
        "model": codex_default_model,
        "model_reasoning_effort": "high",
        "model_reasoning_summary": "concise",
        "model_verbosity": "high",
    },
    "web": {
        "sandbox_mode": "workspace-write",
        "sandbox_workspace_write": {
            "network_access": True,
        },
        "web_search": "live",
    },
}

BASELINE = {
    "approval_policy": "never",
    "developer_instructions": codex_developer_instructions,
    "model": codex_default_model,
    "model_reasoning_effort": "xhigh",
    "model_reasoning_summary": "none",
    "model_verbosity": "low",
    "notify": ["notify-send", "--app-name", "Codex"],
    "personality": "pragmatic",
    "review_model": codex_default_model,
    "sandbox_mode": "danger-full-access",
    "suppress_unstable_features_warning": True,
    "web_search": "cached",
    "analytics": {
        "enabled": False,
    },
    "features": {
        "apply_patch_freeform": True,
        "child_agents_md": True,
        "enable_fanout": True,
        "hooks": True,
        "multi_agent": True,
        "undo": True,
    },
    "sandbox_workspace_write": {
        "exclude_slash_tmp": False,
        "exclude_tmpdir_env_var": False,
        "network_access": True,
    },
    "tools": {
        "view_image": True,
    },
    "tui": {
        "show_tooltips": False,
    },
    "projects": build_trusted_project_entries(),
    "mcp_servers": build_mcp_server_entries(),
}

config_path = pathlib.Path(os.path.expanduser("~/.codex/config.toml"))
config_path.parent.mkdir(parents=True, exist_ok=True)

raw = b""
if config_path.exists():
    raw = config_path.read_bytes()

try:
    data = tomllib.loads(raw.decode("utf-8")) if raw else {}
except Exception:
    bak = config_path.with_suffix(".toml.bak")
    try:
        config_path.replace(bak)
    except Exception:
        pass
    data = {}


def deep_merge(base: dict[str, Any], overlay: dict[str, Any]) -> None:
    for key, value in overlay.items():
        if isinstance(value, dict) and isinstance(base.get(key), dict):
            deep_merge(base[key], value)
        else:
            base[key] = value


deep_merge(data, BASELINE)

data.pop("profile", None)
data.pop("profiles", None)

existing_mcp_servers = data.setdefault("mcp_servers", {})
for generated_server_name, generated_server_entry in build_mcp_server_entries().items():
    existing_mcp_servers[generated_server_name] = generated_server_entry

config_path.write_text(render_codex_config_toml(data), encoding="utf-8")

for profile_name, profile_overrides in PROFILE_OVERRIDES.items():
    profile_config_path = config_path.parent / f"{profile_name}.config.toml"
    profile_config_path.write_text(
        render_codex_config_toml(profile_overrides), encoding="utf-8"
    )
