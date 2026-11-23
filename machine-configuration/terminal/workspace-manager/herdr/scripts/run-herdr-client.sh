installed_executable="$1"
shift
running_server_record=""
if [[ -e /proc/self/exe ]]; then
  running_server_record="${XDG_STATE_HOME:-${HOME:-}/.local/state}/herdr/running-server-client"
fi

running_server_is_installed_executable() {
  local recorded_socket recorded_process server_status
  [[ -r $running_server_record ]] || return 1
  { read -r recorded_socket && read -r recorded_process; } <"$running_server_record" || return 1
  [[ $recorded_process =~ ^[0-9]+$ ]] || return 1
  server_status="$("$installed_executable" status server --json 2>/dev/null)" || return 1
  [[ $server_status =~ \"socket\":\"([^\"\\]+)\" ]] || return 1
  [[ ${BASH_REMATCH[1]} == "$recorded_socket" ]] || return 1
  [[ $running_server_record -nt $recorded_socket ]] || return 1
  [[ /proc/$recorded_process/exe -ef $installed_executable ]]
}

if running_server_is_installed_executable; then
  exec "$installed_executable" "$@"
fi

selected_executable="$(
  HERDR_RUNNING_SERVER_RECORD="$running_server_record" \
    select-herdr-client select "$installed_executable" "$@"
)"
exec "$selected_executable" "$@"
