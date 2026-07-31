{
  config,
  lib,
  pkgs,
  ...
}:
let
  interactiveSessionOnlySystemPromptSurfaces =
    pkgs.writeText "claude-interactive-session-only-system-prompt-surfaces.md"
      (
        builtins.readFile ../../../../agents/core_rules/communication/interactive-preferences.md
        + "\n"
        + builtins.readFile ../../../../agents/core_rules/communication/enforced-reply-rules.md
        + "\n"
        + builtins.readFile ../../../../agents/core_rules/adaptive-implementation-delivery-process.md
      );

  claudeWorkspaceScript = pkgs.writeShellScriptBin "claude-workspace" ''
    export CLAUDE_BINARY_PATH="${lib.getExe config.claude.package}"
    export CLAUDE_INTERACTIVE_PREFERENCES_PATH="${interactiveSessionOnlySystemPromptSurfaces}"
    export CLAUDE_INTERACTIVE_MODEL="claude-opus-5[1m]"
    export CLAUDE_CODE_EFFORT_LEVEL="max"
    exec ${pkgs.python312}/bin/python3 ${./scripts/launch-claude-workspace-session} "$@"
  '';
in
{
  home.packages = [ claudeWorkspaceScript ];
}
