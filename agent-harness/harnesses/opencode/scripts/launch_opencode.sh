opencodeConfigOverlayFile="@interactiveSessionConfigOverlay@"

applyInteractiveSessionOverlay() {
  @workspaceProfileLaunchDispatch@
  export OPENCODE_CONFIG="$opencodeConfigOverlayFile"
  export AGENT_INTERACTIVE_PREFERENCES_PATH="@interactivePreferencesFile@"
}

case "${1:-}" in
  acp | api | auth | completion | debug | mcp | models | plugin | reload | serve | service | session | stats | uninstall | update | upgrade | pair | run)
    ;;
  *)
    applyInteractiveSessionOverlay
    ;;
esac
exec @opencodeAuthenticated@/bin/opencode "$@"
