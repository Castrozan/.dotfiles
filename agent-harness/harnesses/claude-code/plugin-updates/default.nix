{
  config,
  lib,
  pkgs,
  ...
}:
let
  settingsOverlayFile = import ../workspace-profile-settings-overlay.nix { inherit pkgs; };

  enabledPluginSettingsFiles = [
    "${config.home.homeDirectory}/.claude/settings.json.nix-source"
  ]
  ++ map settingsOverlayFile (
    lib.filter (
      workspaceProfile: workspaceProfile.claudeCode ? settingsOverlay
    ) config.agentWorkspaceProfiles.profiles
  );
in
{
  home.activation.updateEnabledClaudePlugins = {
    after = [ "seedClaudeSettingsAsMutableFile" ];
    before = [ ];
    data = ''
      PATH="${config.claude.unwrappedPackage}/bin:$PATH" \
        ${pkgs.python312}/bin/python3 ${./update_enabled_plugins.py} \
        ${lib.escapeShellArgs enabledPluginSettingsFiles}
    '';
  };
}
