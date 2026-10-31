{
  config,
  lib,
  pkgs,
  ...
}:
let
  claudeConfigDirectory = "${config.home.homeDirectory}/.claude";
  retiredMarketplaces = [
    "claude-image-view"
    "dotfiles-mods"
    "jarrodwatts-claude-stt"
  ];
in
{
  home.activation.removeRetiredClaudeMarketplaces =
    lib.hm.dag.entryBetween [ "seedClaudeSettingsAsMutableFile" ] [ "writeBoundary" ]
      ''
        for retiredMarketplace in ${lib.escapeShellArgs retiredMarketplaces}; do
          if ${pkgs.jq}/bin/jq -e --arg marketplace "$retiredMarketplace" 'has($marketplace)' "${claudeConfigDirectory}/plugins/known_marketplaces.json" >/dev/null 2>&1; then
            CLAUDE_CONFIG_DIR="${claudeConfigDirectory}" ${config.claude.unwrappedPackage}/bin/claude plugin marketplace remove "$retiredMarketplace"
          fi
        done
      '';
}
