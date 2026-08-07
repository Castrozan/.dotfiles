{
  pkgs,
  lib,
  interactiveSessionDeveloperInstructionsText,
}:
let
  developerInstructionsFile =
    workspaceProfile:
    pkgs.writeText "codex-workspace-profile-${workspaceProfile.name}-developer-instructions.md" (
      lib.concatStringsSep "\n" (
        [ interactiveSessionDeveloperInstructionsText ]
        ++ map builtins.readFile workspaceProfile.instructionFiles
      )
    );

  configOverrideArguments =
    workspaceProfile:
    lib.concatStringsSep " " (
      lib.mapAttrsToList (
        overrideKey: overrideValue: "-c ${lib.escapeShellArg "${overrideKey}=${toString overrideValue}"}"
      ) (workspaceProfile.codex.configOverrides or { })
    );
in
{
  activationShellStatementsForProfile =
    workspaceProfile:
    lib.concatStrings [
      (lib.optionalString (workspaceProfile.instructionFiles != [ ]) ''
        codexDeveloperInstructionsFile=${developerInstructionsFile workspaceProfile}
      '')
      (lib.optionalString (workspaceProfile.codex.configOverrides or { } != { }) ''
        workspaceProfileArguments+=(${configOverrideArguments workspaceProfile})
      '')
    ];
}
