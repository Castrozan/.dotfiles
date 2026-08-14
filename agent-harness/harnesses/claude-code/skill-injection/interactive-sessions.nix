{
  config,
  lib,
  pkgs,
  ...
}:
let
  interactiveSessionSystemPromptText = lib.concatStringsSep "\n" [
    (builtins.readFile ../../../../agent-harness/agent-instructions/core-rules/communication/interactive-hook-communication.md)
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

  claudeInteractiveScript = pkgs.writeShellScriptBin "claude" ''
    claudeSystemPromptFile="${interactiveSessionOnlySystemPromptSurfaces}"
    workspaceProfileArguments=()
    ${workspaceProfileLaunchDispatch}
    export CLAUDE_INTERACTIVE_PREFERENCES_PATH="$claudeSystemPromptFile"
    exec ${lib.getExe config.claude.unwrappedPackage} \
      --append-system-prompt-file "$claudeSystemPromptFile" \
      "''${workspaceProfileArguments[@]}" \
      "$@"
  '';
in
{
  options.claude.package = lib.mkOption {
    type = lib.types.package;
    default = claudeInteractiveScript;
    readOnly = true;
    description = "The claude every keyboard-driven launch resolves, wrapping the unwrapped package with the human's own reply-shape system prompt and the resolved workspace profile. It carries the plain `claude` name so a herdr agent, a script or a launcher gets the same surface the human's shell does.";
  };

  config.home = {
    packages = [ claudeInteractiveScript ];
    file.".local/bin/claude" = {
      source = "${claudeInteractiveScript}/bin/claude";
      force = true;
    };
  };
}
