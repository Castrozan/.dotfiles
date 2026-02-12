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

if [[ "${mode}" == "click" ]]; then
  activeWorkspace=$(hyprctl activeworkspace -j | jq -r '.id // empty')
  if [[ -z "${activeWorkspace}" ]]; then
    exit 1
  fi
  pageStart=$(( ((activeWorkspace - 1) / 7) * 7 + 1 ))
  targetWorkspace=$(( pageStart + slot - 1 ))
  hyprctl dispatch workspace "${targetWorkspace}" >/dev/null
  exit 0
fi

computeAndOutput() {
  local activeWorkspace
  activeWorkspace=$(hyprctl activeworkspace -j | jq -r '.id // empty') || return
  [[ -z "${activeWorkspace}" ]] && return

  local pageStart=$(( ((activeWorkspace - 1) / 7) * 7 + 1 ))
  local targetWorkspace=$(( pageStart + slot - 1 ))

  local workspacesJson
  workspacesJson=$(hyprctl workspaces -j) || return
  local windowCount
  windowCount=$(printf '%s' "${workspacesJson}" | jq -r --argjson t "${targetWorkspace}" '[.[] | select(.id == $t) | .windows][0] // 0')

  local cssClass=""
  if (( activeWorkspace == targetWorkspace )); then
    cssClass="active"
  elif (( windowCount > 0 )); then
    cssClass="occupied"
  else
    cssClass="empty"
  fi

  printf '{"text":"%s","class":"%s"}\n' "${targetWorkspace}" "${cssClass}"
}

computeAndOutput

socketPath="${XDG_RUNTIME_DIR}/hypr/${HYPRLAND_INSTANCE_SIGNATURE}/.socket2.sock"
nc -U "${socketPath}" 2>/dev/null | while IFS= read -r event; do
  case "${event}" in
    workspace*|movewindow*|createworkspace*|destroyworkspace*|focusedmon*)
      computeAndOutput
      ;;
  esac
done
