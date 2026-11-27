{
  config,
  lib,
  pkgs,
  ...
}:
let
  claudeConfigDirectory = "${config.home.homeDirectory}/.claude";
in
{
  home.activation.reconcileDeclaredClaudeMarketplaceSources = {
    after = [ "seedClaudeSettingsAsMutableFile" ];
    before = [ "updateEnabledClaudePlugins" ];
    data = ''
      PATH="${pkgs.git}/bin:$PATH" ${pkgs.python312}/bin/python3 ${./reconcile_declared_marketplace_sources.py} \
        ${lib.escapeShellArg "${claudeConfigDirectory}/plugins/known_marketplaces.json"} \
        ${lib.escapeShellArg "${claudeConfigDirectory}/settings.json"} \
        ${lib.escapeShellArg "${claudeConfigDirectory}/settings.json.nix-source"}
    '';
  };
}
