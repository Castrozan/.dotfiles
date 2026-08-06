{
  pkgs,
  lib,
  interactiveSessionSystemPromptText,
}:
let
  settingsOverlayFile =
    workspaceProfile:
    pkgs.writeText "claude-workspace-profile-${workspaceProfile.name}-settings.json" (
      builtins.toJSON workspaceProfile.claudeCode.settingsOverlay
    );

  systemPromptFile =
    workspaceProfile:
    pkgs.writeText "claude-workspace-profile-${workspaceProfile.name}-system-prompt.md" (
      lib.concatStringsSep "\n" (
        [ interactiveSessionSystemPromptText ] ++ map builtins.readFile workspaceProfile.instructionFiles
      )
    );

  pluginDirectoryArguments =
    workspaceProfile:
    lib.concatMapStringsSep " " (
      pluginDirectory: "--plugin-dir ${lib.escapeShellArg pluginDirectory}"
    ) (workspaceProfile.claudeCode.pluginDirectories or [ ]);
in
{
  activationShellStatementsForProfile =
    workspaceProfile:
    lib.concatStrings [
      (lib.optionalString (workspaceProfile.claudeCode ? settingsOverlay) ''
        workspaceProfileArguments+=(--settings ${settingsOverlayFile workspaceProfile})
      '')
      (lib.optionalString (workspaceProfile.claudeCode.pluginDirectories or [ ] != [ ]) ''
        workspaceProfileArguments+=(${pluginDirectoryArguments workspaceProfile})
      '')
      (lib.optionalString (workspaceProfile.instructionFiles != [ ]) ''
        claudeSystemPromptFile=${systemPromptFile workspaceProfile}
      '')
    ];
}
