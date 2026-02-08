import os
import pathlib
import tomllib

BASELINE = {
    "approval_policy": "never",
    "sandbox_mode": "workspace-write",
    "web_search": "cached",
    "sandbox_workspace_write": {
        "exclude_slash_tmp": False,
        "exclude_tmpdir_env_var": False,
        "network_access": True,
    },
    "tools": {
        "view_image": True,
    },
    "profiles": {
        "deep": {
            "model_reasoning_effort": "high",
            "model_verbosity": "high",
        },
    },
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


def deep_merge(base, overlay):
    for key, value in overlay.items():
        if isinstance(value, dict) and isinstance(base.get(key), dict):
            deep_merge(base[key], value)
        else:
            base[key] = value


deep_merge(data, BASELINE)


def toml_quote(s: str) -> str:
    return '"' + s.replace("\\", "\\\\").replace('"', '\\"') + '"'


def toml_value(v):
    if v is None:
        return "null"
    if isinstance(v, bool):
        return "true" if v else "false"
    if isinstance(v, int):
        return str(v)
    if isinstance(v, float):
        return repr(v)
    if isinstance(v, str):
        return toml_quote(v)
    if isinstance(v, list):
        return "[" + ", ".join(toml_value(x) for x in v) + "]"
    if isinstance(v, dict):
        items = ", ".join(f"{k} = {toml_value(vv)}" for k, vv in sorted(v.items()))
        return "{ " + items + " }"
    raise TypeError(type(v))


def emit_table_header(parts):
    out = []
    for p in parts:
        if any(c in p for c in "/\\:") or p.startswith(("~", ".", " ")):
            out.append(toml_quote(p))
        else:
            out.append(p)
    return "[" + ".".join(out) + "]"


NESTED_TABLES = {"projects", "profiles", "features", "analytics", "sandbox_workspace_write", "tools"}

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

config_path.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")
