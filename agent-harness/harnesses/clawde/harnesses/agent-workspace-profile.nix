{ config, lib }:
let
  inherit (import ../../../workspace-profiles/activation/harness-launch-dispatch.nix { inherit lib; })
    sessionEnvironmentAssignmentsForProfile
    ;

  workspaceProfilesCarryingClaudeSettings = lib.filter (
    workspaceProfile: workspaceProfile.claudeCode ? settingsOverlay
  ) (config.agentWorkspaceProfiles.profiles or [ ]);

  workspaceProfileNamed =
    profileName:
    lib.findFirst (
      workspaceProfile: workspaceProfile.name == profileName
    ) (throw "no workspace profile named ${profileName}") workspaceProfilesCarryingClaudeSettings;
in
{
  inherit workspaceProfilesCarryingClaudeSettings;

  claudeSettingsOverlayOf =
    agent:
    lib.optionalAttrs (agent.claudeSettingsWorkspaceProfile != null) (
      (workspaceProfileNamed agent.claudeSettingsWorkspaceProfile).claudeCode.settingsOverlay
    );

  sessionEnvironmentAssignmentsOf =
    agent:
    lib.optionalString (agent.claudeSettingsWorkspaceProfile != null) (
      sessionEnvironmentAssignmentsForProfile (workspaceProfileNamed agent.claudeSettingsWorkspaceProfile)
    );
}
