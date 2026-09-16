{ pkgs }:
workspaceProfile:
pkgs.writeText "claude-workspace-profile-${workspaceProfile.name}-settings.json" (
  builtins.toJSON workspaceProfile.claudeCode.settingsOverlay
)
