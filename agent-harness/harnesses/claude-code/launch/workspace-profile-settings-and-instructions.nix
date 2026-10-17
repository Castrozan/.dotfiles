{
  pkgs,
  lib,
  interactiveSessionOnlySystemPromptSurfaces,
  interactiveSessionSettings,
}:
let
  interactiveSessionSettingsFileForProfile =
    workspaceProfile:
    pkgs.writeText "claude-workspace-profile-${workspaceProfile.name}-interactive-settings.json" (
      builtins.toJSON (
        lib.recursiveUpdate interactiveSessionSettings workspaceProfile.claudeCode.settingsOverlay
      )
    );

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
        claudeSettingsFile=${interactiveSessionSettingsFileForProfile workspaceProfile}
      '')
      (lib.optionalString (workspaceProfile.instructionFiles != [ ]) ''
        claudeSystemPromptFile=${systemPromptFile workspaceProfile}
      '')
    ];
}
