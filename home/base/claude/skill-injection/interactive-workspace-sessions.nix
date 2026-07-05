{
  config,
  lib,
  pkgs,
  ...
}:
let
  defaultClaudeFishFunction = ''
    function claude --description "Claude Code with workspace skills"
      command claude-workspace $argv
    end
  '';

  claudeWorkspaceScript = pkgs.writeShellScriptBin "claude-workspace" ''
    export CLAUDE_BINARY_PATH="${lib.getExe config.claude.package}"
    export CLAUDE_INTERACTIVE_PREFERENCES_PATH="${../../../../agents/core_rules/communication/interactive-preferences.md}"
    exec ${pkgs.python312}/bin/python3 ${./scripts/launch-claude-workspace-session} "$@"
  '';
in
{
  home.packages = [ claudeWorkspaceScript ];

  xdg.configFile."fish/conf.d/claude-skill-sets.fish".text = defaultClaudeFishFunction;
}
