{
  pkgs,
  lib,
  interactivePreferencesFile,
}:
let
  configOverlayFile =
    workspaceProfile:
    pkgs.writeText "opencode-workspace-profile-${workspaceProfile.name}-config-overlay.json" (
      builtins.toJSON (
        (workspaceProfile.opencode.configOverlay or { })
        // {
          instructions = [
            "${interactivePreferencesFile}"
          ]
          ++ map toString workspaceProfile.instructionFiles;
        }
      )
    );
in
{
  activationShellStatementsForProfile = workspaceProfile: ''
    opencodeConfigOverlayFile=${configOverlayFile workspaceProfile}
  '';
}
