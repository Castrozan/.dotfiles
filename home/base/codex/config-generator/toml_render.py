from typing import Any


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


def render_codex_config_toml(data: dict[str, Any]) -> str:
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

    return "\n".join(lines).rstrip() + "\n"
