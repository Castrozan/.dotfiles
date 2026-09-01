{
  pkgs,
  lib,
  interactiveSessionSystemPromptText,
}:
let
  settingsOverlayFile = import ./workspace-profile-settings-overlay.nix { inherit pkgs; };

  systemPromptFile =
    workspaceProfile:
    pkgs.writeText "claude-workspace-profile-${workspaceProfile.name}-system-prompt.md" (
      lib.concatStringsSep "\n" (
        [ interactiveSessionSystemPromptText ] ++ map builtins.readFile workspaceProfile.instructionFiles
      )
    );
in
{
  activationShellStatementsForProfile =
    workspaceProfile:
    lib.concatStrings [
      (lib.optionalString (workspaceProfile.claudeCode ? settingsOverlay) ''
        workspaceProfileArguments+=(--settings ${settingsOverlayFile workspaceProfile})
      '')
      (lib.optionalString (workspaceProfile.instructionFiles != [ ]) ''
        claudeSystemPromptFile=${systemPromptFile workspaceProfile}
      '')
    ];
}
