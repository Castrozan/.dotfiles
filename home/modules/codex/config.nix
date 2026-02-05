{ pkgs, ... }:
let
  python = pkgs.python3;
in
{
  home = {
    # Codex stores state under ~/.codex (auth, sessions, trust levels).
    # We manage only the baseline config keys and preserve app-managed sections.
    activation.codexBaselineConfig = {
      after = [ "writeBoundary" ];
      before = [ ];
      data = ''
        set -euo pipefail

        CODEX_DIR="$HOME/.codex"
        CONFIG="$CODEX_DIR/config.toml"
        mkdir -p "$CODEX_DIR"

        # Patch in a baseline config while preserving Codex-managed data like:
        #   [projects."..."] trust_level = "trusted"
        ${python}/bin/python3 - <<'PY'
import os
import pathlib
import sys
import tomllib

config_path = pathlib.Path(os.path.expanduser("~/.codex/config.toml"))
config_path.parent.mkdir(parents=True, exist_ok=True)

raw = b""
if config_path.exists():
    raw = config_path.read_bytes()

try:
    data = tomllib.loads(raw.decode("utf-8")) if raw else {}
except Exception as e:
    # If the file ever gets corrupted, preserve it and start fresh.
    bak = config_path.with_suffix(".toml.bak")
    try:
        config_path.replace(bak)
    except Exception:
        pass
    data = {}

def ensure_table(root, key):
    v = root.get(key)
    if not isinstance(v, dict):
        v = {}
        root[key] = v
    return v

# Baseline defaults (safe + predictable). Users can override via CLI flags or profiles.
data["model"] = "gpt-5.3-codex"
data["review_model"] = data.get("review_model") or "gpt-5.3-codex"
data["profile"] = data.get("profile") or "fast"
data["approval_policy"] = "on-failure"
data["sandbox_mode"] = "workspace-write"
data["model_reasoning_effort"] = data.get("model_reasoning_effort") or "medium"
data["model_verbosity"] = data.get("model_verbosity") or "medium"
data["model_reasoning_summary"] = data.get("model_reasoning_summary") or "auto"
data["model_auto_compact_token_limit"] = data.get("model_auto_compact_token_limit") or 60000
data["model_context_window"] = data.get("model_context_window") or 120000
data["web_search"] = data.get("web_search") or "cached"

data["developer_instructions"] = data.get("developer_instructions") or (
    "Operate pragmatically: keep diffs small, verify with fast checks, and prefer repo-local truth "
    "(AGENTS.md, bin/, home/modules/). Use profiles: fast (default), deep, web."
)

analytics = ensure_table(data, "analytics")
analytics["enabled"] = False

tools = ensure_table(data, "tools")
tools.setdefault("web_search", True)
tools.setdefault("view_image", True)

sandbox_ww = ensure_table(data, "sandbox_workspace_write")
sandbox_ww.setdefault("exclude_slash_tmp", True)
sandbox_ww.setdefault("exclude_tmpdir_env_var", True)
sandbox_ww.setdefault("network_access", False)
sandbox_ww.setdefault("writable_roots", [])

features = ensure_table(data, "features")
features.setdefault("undo", True)
features.setdefault("apply_patch_freeform", True)
features.setdefault("child_agents_md", True)

profiles = ensure_table(data, "profiles")
profiles.setdefault("fast", {})
profiles["fast"].update({
    "model_reasoning_effort": "low",
    "model_verbosity": "low",
    "model_reasoning_summary": "none",
})
profiles.setdefault("deep", {})
profiles["deep"].update({
    "model_reasoning_effort": "high",
    "model_verbosity": "high",
    "model_reasoning_summary": "concise",
})
profiles.setdefault("web", {})
profiles["web"].update({
    "web_search": "live",
    "sandbox_mode": "workspace-write",
    "sandbox_workspace_write": {
        "network_access": True,
    },
})

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
        # Inline table for small nested blobs.
        items = ", ".join(f"{k} = {toml_value(vv)}" for k, vv in sorted(v.items()))
        return "{ " + items + " }"
    raise TypeError(type(v))

def emit_table_header(parts):
    # Quote parts that are paths (projects key) or contain slashes.
    out = []
    for p in parts:
        if any(c in p for c in '/\\:') or p.startswith("~") or p.startswith(".") or p.startswith(" "):
            out.append(toml_quote(p))
        else:
            out.append(p)
    return "[" + ".".join(out) + "]"

top_skip = {"projects", "profiles", "features", "analytics", "sandbox_workspace_write", "tools"}
lines = []

for k in sorted(data.keys()):
    if k in top_skip:
        continue
    if isinstance(data[k], dict):
        continue
    lines.append(f"{k} = {toml_value(data[k])}")

def emit_simple_table(name):
    tbl = data.get(name)
    if not isinstance(tbl, dict) or not tbl:
        return
    lines.append("")
    lines.append(f"[{name}]")
    for k, v in sorted(tbl.items()):
        lines.append(f"{k} = {toml_value(v)}")

emit_simple_table("analytics")
emit_simple_table("tools")
emit_simple_table("sandbox_workspace_write")
emit_simple_table("features")

if isinstance(profiles, dict) and profiles:
    for prof in sorted(profiles.keys()):
        val = profiles[prof]
        if not isinstance(val, dict):
            continue
        lines.append("")
        lines.append("[profiles." + prof + "]")
        for k, v in sorted(val.items()):
            if isinstance(v, dict):
                lines.append(f"{k} = {toml_value(v)}")
            else:
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
PY
      '';
    };
  };
}
