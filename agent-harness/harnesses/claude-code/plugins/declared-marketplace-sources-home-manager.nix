{
  config,
  lib,
  pkgs,
  ...
}:
let
  claudeConfigDirectory = "${config.home.homeDirectory}/.claude";

  settingsOverlayFile = import ../settings/workspace-profile-settings-json.nix { inherit pkgs; };

  workspaceProfileSettingsOverlayFiles = map settingsOverlayFile (
    lib.filter (
      workspaceProfile: workspaceProfile.claudeCode ? settingsOverlay
    ) config.agentWorkspaceProfiles.profiles
  );
in
{
  home.activation.reconcileDeclaredClaudeMarketplaceSources = {
    after = [ "seedClaudeSettingsAsMutableFile" ];
    before = [ "updateEnabledClaudePlugins" ];
    data = ''
      PATH="${pkgs.git}/bin:$PATH" ${pkgs.python312}/bin/python3 ${./reconcile_declared_marketplace_sources.py} \
        ${lib.escapeShellArg "${claudeConfigDirectory}/plugins/known_marketplaces.json"} \
        ${lib.escapeShellArg "${claudeConfigDirectory}/settings.json"} \
        ${lib.escapeShellArgs workspaceProfileSettingsOverlayFiles}
    '';
  };
}
