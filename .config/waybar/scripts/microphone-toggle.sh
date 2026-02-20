#!/usr/bin/env bash
set -Eeuo pipefail

readonly MIC_SOURCE_ID="38"

_get_mute_status() {
  pactl get-source-mute "${MIC_SOURCE_ID}" | grep -q "yes" && echo "muted" || echo "unmuted"
}

_get_volume() {
  pactl get-source-volume "${MIC_SOURCE_ID}" | head -n1 | awk '{print $5}' | sed 's/%//'
}

_output_json() {
  local status
  status="$(_get_mute_status)"
  local volume
  volume="$(_get_volume)"
  
  if [[ "${status}" == "muted" ]]; then
    echo "{\"text\":\"󰍭\",\"class\":\"muted\",\"tooltip\":\"Microphone muted\"}"
  else
    echo "{\"text\":\"󰍬\",\"class\":\"unmuted\",\"tooltip\":\"Microphone unmuted (${volume}%)\"}"
  fi
}

_toggle() {
  wpctl set-mute "${MIC_SOURCE_ID}" toggle
}

main() {
  case "${1:-status}" in
    status)
      _output_json
      ;;
    toggle)
      _toggle
      ;;
    *)
      echo "Usage: $0 {status|toggle}" >&2
      exit 1
      ;;
  esac
}

main "$@"
