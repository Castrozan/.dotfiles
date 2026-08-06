{
  config,
  lib,
  pkgs,
  ...
}:
let
  interactiveSessionSystemPromptText = lib.concatStringsSep "\n" [
    (builtins.readFile ../../../../agent-harness/agent-instructions/core-rules/communication/interactive-preferences.md)
    (builtins.readFile ../../../../agent-harness/agent-instructions/core-rules/communication/enforced-reply-rules.md)
    (builtins.readFile ../../../../agent-harness/agent-instructions/core-rules/adaptive-implementation-delivery-process.md)
  ];

  interactiveSessionOnlySystemPromptSurfaces = pkgs.writeText "claude-interactive-session-only-system-prompt-surfaces.md" interactiveSessionSystemPromptText;

  workspaceProfileActivation = import ../workspace-profile-activation.nix {
    inherit pkgs lib interactiveSessionSystemPromptText;
  };

  inherit (import ../../../workspace-profiles/activation/harness-launch-dispatch.nix { inherit lib; })
    mkWorkspaceProfileLaunchDispatch
    ;

  workspaceProfileLaunchDispatch = mkWorkspaceProfileLaunchDispatch {
    inherit (config) agentWorkspaceProfiles;
    inherit (workspaceProfileActivation) activationShellStatementsForProfile;
  };

  claudeInteractiveScript = pkgs.writeShellScriptBin "claude-interactive" ''
    claudeSystemPromptFile="${interactiveSessionOnlySystemPromptSurfaces}"
    workspaceProfileArguments=()
    ${workspaceProfileLaunchDispatch}
    export CLAUDE_INTERACTIVE_PREFERENCES_PATH="$claudeSystemPromptFile"
    exec ${lib.getExe config.claude.package} \
      --append-system-prompt-file "$claudeSystemPromptFile" \
      "''${workspaceProfileArguments[@]}" \
      "$@"
  '';
in
{
  home.packages = [ claudeInteractiveScript ];
}
