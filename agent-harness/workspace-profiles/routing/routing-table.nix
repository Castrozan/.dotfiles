{ pkgs, workspaceProfiles }:
pkgs.writeText "agent-workspace-profile-routing-table.json" (
  builtins.toJSON {
    profiles = map (workspaceProfile: {
      inherit (workspaceProfile) name directoryPrefixes gitRemotePatterns;
    }) workspaceProfiles;
  }
)
