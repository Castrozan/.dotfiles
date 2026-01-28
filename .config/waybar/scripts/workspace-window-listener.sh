#!/usr/bin/env bash
set -euo pipefail

state_dir="${XDG_RUNTIME_DIR:-/tmp}/waybar"
state_file="${state_dir}/workspace-window.json"

mkdir -p "${state_dir}"

printf '{"text":""}\n'

render() {
  local active_workspace start target workspace_json exists windows class slot

  active_workspace=$(hyprctl activeworkspace -j | jq -r '.id // empty')
  if [[ -z "${active_workspace}" ]]; then
    return
  fi

  start=$(( ((active_workspace - 1) / 7) * 7 + 1 ))
  workspace_json=$(hyprctl workspaces -j)

  for slot in {1..7}; do
    target=$(( start + slot - 1 ))
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

    printf '{"slot":%s,"text":"%s","class":"%s"}\n' "${slot}" "${target}" "${class}"
  done | jq -s '.' > "${state_file}.tmp"

  mv "${state_file}.tmp" "${state_file}"
  pkill -RTMIN+8 waybar 2>/dev/null || true
}

render

if [[ "${1:-}" == "--once" ]]; then
  exit 0
fi

socat -u "UNIX-CONNECT:${XDG_RUNTIME_DIR}/hypr/${HYPRLAND_INSTANCE_SIGNATURE}/.socket2.sock" - \
  | while read -r _; do
    render
  done
