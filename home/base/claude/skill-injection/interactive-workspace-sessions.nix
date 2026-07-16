{
  config,
  lib,
  pkgs,
  ...
}:
let
  claudeWorkspaceScript = pkgs.writeShellScriptBin "claude-workspace" ''
    export CLAUDE_BINARY_PATH="${lib.getExe config.claude.package}"
    export CLAUDE_INTERACTIVE_PREFERENCES_PATH="${../../../../agents/core_rules/communication/interactive-preferences.md}"
    export CLAUDE_INTERACTIVE_MODEL="claude-opus-4-8[1m]"
    exec ${pkgs.python312}/bin/python3 ${./scripts/launch-claude-workspace-session} "$@"
  '';
in
{
  home.packages = [ claudeWorkspaceScript ];
}
