#!/usr/bin/env bash
set -euo pipefail

mode="render"
slot="${1:-}"

if [[ "${1:-}" == "--click" ]]; then
  mode="click"
  slot="${2:-}"
fi

if [[ -z "${slot}" || ! "${slot}" =~ ^[1-7]$ ]]; then
  exit 1
fi

active_workspace=$(hyprctl activeworkspace -j | jq -r '.id // empty')
if [[ -z "${active_workspace}" ]]; then
  exit 1
fi

start=$(( ((active_workspace - 1) / 7) * 7 + 1 ))
target=$(( start + slot - 1 ))

if [[ "${mode}" == "click" ]]; then
  hyprctl dispatch workspace "${target}" >/dev/null
  exit 0
fi

workspace_json=$(hyprctl workspaces -j)
exists=$(printf '%s' "${workspace_json}" | jq -r --argjson target "${target}" 'map(.id) | index($target) != null')
windows=$(printf '%s' "${workspace_json}" | jq -r --argjson target "${target}" 'map(select(.id == $target) | .windows) | .[0] // 0')

class=""
if [[ "${active_workspace}" -eq "${target}" ]]; then
  class="active"
elif [[ "${windows}" -gt 0 ]]; then
  class="occupied"
elif [[ "${exists}" != "true" ]]; then
  class="empty"
fi

printf '{"text":"%s","class":"%s"}\n' "${target}" "${class}"
