opencodeConfigOverlayFile="@interactiveSessionConfigOverlay@"

applyInteractiveSessionOverlay() {
  @workspaceProfileLaunchDispatch@
  export OPENCODE_CONFIG="$opencodeConfigOverlayFile"
  export AGENT_INTERACTIVE_PREFERENCES_PATH="@interactivePreferencesFile@"
}

case "${1:-}" in
  acp | api | auth | completion | debug | mcp | models | plugin | reload | serve | service | session | stats | uninstall | update | upgrade | pair | run)
    ;;
  mini)
    applyInteractiveSessionOverlay
    shift
    set -- mini --standalone "$@"
    ;;
  *)
    applyInteractiveSessionOverlay
    set -- --standalone "$@"
    ;;
esac
exec @opencodeAuthenticated@/bin/opencode "$@"
