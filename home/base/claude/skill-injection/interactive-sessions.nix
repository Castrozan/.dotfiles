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
        builtins.readFile ../../../../agent-harness/agent-instructions/core-rules/communication/interactive-preferences.md
        + "\n"
        + builtins.readFile ../../../../agent-harness/agent-instructions/core-rules/communication/enforced-reply-rules.md
        + "\n"
        + builtins.readFile ../../../../agent-harness/agent-instructions/core-rules/adaptive-implementation-delivery-process.md
      );

  claudeInteractiveScript = pkgs.writeShellScriptBin "claude-interactive" ''
    export CLAUDE_INTERACTIVE_PREFERENCES_PATH="${interactiveSessionOnlySystemPromptSurfaces}"
    exec ${lib.getExe config.claude.package} \
      --append-system-prompt-file "${interactiveSessionOnlySystemPromptSurfaces}" "$@"
  '';
in
{
  home.packages = [ claudeInteractiveScript ];
}
