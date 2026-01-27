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

state_file="${XDG_RUNTIME_DIR:-/tmp}/waybar/workspace-window.json"

if [[ "${mode}" == "click" ]]; then
  active_workspace=$(hyprctl activeworkspace -j | jq -r '.id // empty')
  if [[ -z "${active_workspace}" ]]; then
    exit 1
  fi
  start=$(( ((active_workspace - 1) / 7) * 7 + 1 ))
  target=$(( start + slot - 1 ))
  hyprctl dispatch workspace "${target}" >/dev/null
  exit 0
fi

if [[ ! -f "${state_file}" ]]; then
  echo '{"text":"?","class":"empty"}'
  exit 0
fi

entry=$(jq -r --argjson slot "${slot}" '.[] | select(.slot == $slot)' "${state_file}")
if [[ -z "${entry}" || "${entry}" == "null" ]]; then
  echo '{"text":"?","class":"empty"}'
  exit 0
fi

text=$(printf '%s' "${entry}" | jq -r '.text')
class=$(printf '%s' "${entry}" | jq -r '.class')

printf '{"text":"%s","class":"%s"}\n' "${text}" "${class}"
