import os
import pathlib
import tomllib
from typing import Any

codex_default_model = os.environ.get("CODEX_DEFAULT_MODEL", "gpt-5.4")
codex_developer_instructions = os.environ.get(
    "CODEX_DEVELOPER_INSTRUCTIONS",
    (
        "Operate pragmatically: keep diffs small, verify with fast checks, and "
        "prefer repo-local truth (AGENTS.md, bin/, home/modules/). Use profiles: "
        "fast (default), deep, web."
    ),
)
chrome_devtools_mcp_command = os.environ.get(
    "CODEX_CHROME_DEVTOOLS_MCP_COMMAND",
    "chrome-devtools-mcp",
)
chromium_executable_path = os.environ.get(
    "CODEX_CHROMIUM_EXECUTABLE_PATH",
    "chromium",
)
scrapling_fetch_mcp_command = os.environ.get(
    "CODEX_SCRAPLING_FETCH_MCP_COMMAND",
    str(pathlib.Path.home() / ".local" / "bin" / "scrapling-mcp"),
)


def build_trusted_project_entries() -> dict[str, dict[str, str]]:
    home_directory = pathlib.Path.home()
    trusted_project_entries = {
        str(home_directory): {"trust_level": "trusted"},
        str(home_directory / ".dotfiles"): {"trust_level": "trusted"},
    }

    for trusted_parent_directory in [
        home_directory / "repo",
        home_directory / "betha-fly" / "projects",
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
        "chrome-devtools-live": {
            "command": chrome_devtools_mcp_command,
            "args": [
                "--autoConnect",
                "--usageStatistics",
                "false",
            ],
        },
        "chrome-devtools-headless": {
            "command": chrome_devtools_mcp_command,
            "args": [
                "--headless",
                "--executablePath",
                chromium_executable_path,
                "--usageStatistics",
                "false",
            ],
        },
        "scrapling-fetch": {
            "command": scrapling_fetch_mcp_command,
            "args": [],
        },
    }


BASELINE = {
    "approval_policy": "never",
    "developer_instructions": codex_developer_instructions,
    "model": codex_default_model,
    "model_reasoning_effort": "medium",
    "model_reasoning_summary": "auto",
    "model_verbosity": "medium",
    "notify": ["notify-send", "--app-name", "Codex"],
    "personality": "pragmatic",
    "profile": "fast",
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
    "profiles": {
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


def toml_quote(value: str) -> str:
    return '"' + value.replace("\\", "\\\\").replace('"', '\\"') + '"'


def toml_value(value: Any) -> str:
    if value is None:
        return "null"
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, int):
        return str(value)
    if isinstance(value, float):
        return repr(value)
    if isinstance(value, str):
        return toml_quote(value)
    if isinstance(value, list):
        return "[" + ", ".join(toml_value(item) for item in value) + "]"
    if isinstance(value, dict):
        items = ", ".join(
            f"{key} = {toml_value(nested_value)}"
            for key, nested_value in sorted(value.items())
        )
        return "{ " + items + " }"
    raise TypeError(type(value))


def emit_table_header(parts: list[str]) -> str:
    out = []
    for part in parts:
        if any(character in part for character in "/\\:") or part.startswith(
            ("~", ".", " ")
        ):
            out.append(toml_quote(part))
        else:
            out.append(part)
    return "[" + ".".join(out) + "]"


NESTED_TABLES = {
    "projects",
    "profiles",
    "features",
    "analytics",
    "mcp_servers",
    "sandbox_workspace_write",
    "tools",
}

lines = []

for k in sorted(data.keys()):
    if k in NESTED_TABLES or isinstance(data[k], dict):
        continue
    lines.append(f"{k} = {toml_value(data[k])}")

for table_name in ["analytics", "tools", "sandbox_workspace_write", "features"]:
    tbl = data.get(table_name)
    if not isinstance(tbl, dict) or not tbl:
        continue
    lines.append("")
    lines.append(f"[{table_name}]")
    for k, v in sorted(tbl.items()):
        lines.append(f"{k} = {toml_value(v)}")

profiles = data.get("profiles")
if isinstance(profiles, dict) and profiles:
    for prof in sorted(profiles.keys()):
        val = profiles[prof]
        if not isinstance(val, dict):
            continue
        lines.append("")
        lines.append(f"[profiles.{prof}]")
        for k, v in sorted(val.items()):
            lines.append(f"{k} = {toml_value(v)}")

projects = data.get("projects")
if isinstance(projects, dict) and projects:
    for path in sorted(projects.keys()):
        val = projects[path]
        if not isinstance(val, dict):
            continue
        lines.append("")
        lines.append(emit_table_header(["projects", path]))
        for k, v in sorted(val.items()):
            lines.append(f"{k} = {toml_value(v)}")

mcp_servers = data.get("mcp_servers")
if isinstance(mcp_servers, dict) and mcp_servers:
    for name in sorted(mcp_servers.keys()):
        val = mcp_servers[name]
        if not isinstance(val, dict):
            continue
        lines.append("")
        lines.append(f"[mcp_servers.{name}]")
        for k, v in sorted(val.items()):
            lines.append(f"{k} = {toml_value(v)}")

config_path.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")
