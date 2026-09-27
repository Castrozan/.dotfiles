opencodeApiKeyFile="@opencodeApiKeyFile@"
if [ -r "$opencodeApiKeyFile" ]; then
  OPENCODE_API_KEY="$(cat "$opencodeApiKeyFile")"
  export OPENCODE_API_KEY
fi

for argument in "$@"; do
  case "$argument" in
    --server | --server=* | --standalone)
      exec @opencodeUnwrapped@/bin/opencode "$@"
      ;;
  esac
done

case "${1:-}" in
  run | mini)
    command="$1"
    shift
    set -- "$command" --standalone "$@"
    ;;
  acp | api | auth | completion | debug | mcp | models | plugin | reload | serve | service | session | stats | uninstall | update | upgrade | pair | --help | -h | --version | -v)
    ;;
  *)
    set -- --standalone "$@"
    ;;
esac
exec @opencodeUnwrapped@/bin/opencode "$@"
