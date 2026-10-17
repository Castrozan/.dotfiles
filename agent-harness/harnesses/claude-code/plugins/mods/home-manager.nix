{
  config,
  lib,
  pkgs,
  ...
}:
let
  claudeModsMarketplace = import ./marketplace.nix { inherit pkgs; };
  claudeWithUserConfigDirectory = ''CLAUDE_CONFIG_DIR="${config.home.homeDirectory}/.claude" ${config.claude.unwrappedPackage}/bin/claude'';
in
{
  home.activation.installClaudeMods =
    lib.hm.dag.entryBetween [ "seedClaudeSettingsAsMutableFile" ] [ "writeBoundary" ]
      ''
        ${claudeWithUserConfigDirectory} plugin marketplace add ${claudeModsMarketplace.marketplace}
        ${lib.concatMapStrings (pluginKey: ''
          ${claudeWithUserConfigDirectory} plugin install ${pluginKey}
        '') claudeModsMarketplace.pluginKeys}
      '';
}
