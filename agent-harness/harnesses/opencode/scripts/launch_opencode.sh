case "$#:${1:-}" in
  1:--help | 1:-h | 1:--version | 1:-v) exec @opencodeAuthenticated@/bin/opencode "$@" ;;
esac

case "${1:-}" in
  acp | api | auth | completion | debug | mcp | models | plugin | reload | serve | service | session | stats | uninstall | update | upgrade | pair | run)
    ;;
  *)
    export OPENCODE_CONFIG="@interactiveSessionConfigOverlay@"
    export AGENT_INTERACTIVE_PREFERENCES_PATH="@interactivePreferencesFile@"
    ;;
esac
exec @opencodeAuthenticated@/bin/opencode "$@"
