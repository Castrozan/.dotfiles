{
  pkgs,
  lib,
  interactiveSessionOnlySystemPromptSurfaces,
}:
let
  settingsOverlayFile = import ../settings/workspace-profile-settings-json.nix { inherit pkgs; };

  systemPromptFile =
    workspaceProfile:
    pkgs.runCommand "claude-workspace-profile-${workspaceProfile.name}-system-prompt.md" { } ''
      for fragment in ${interactiveSessionOnlySystemPromptSurfaces} ${lib.escapeShellArgs (map toString workspaceProfile.instructionFiles)}; do
        cat "$fragment"
        printf '\n'
      done > "$out"
    '';
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
