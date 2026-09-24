{ config, lib, ... }:
{
  imports = [ ../../../agent-instructions/production-plugin/home-manager.nix ];

  home.activation.installProductionClaudePlugin =
    lib.hm.dag.entryAfter
      [
        "linkGeneration"
        "seedClaudeSettingsAsMutableFile"
      ]
      ''
        CLAUDE_CONFIG_DIR="${config.home.homeDirectory}/.claude" \
          ${config.claude.unwrappedPackage}/bin/claude plugin marketplace add "${config.home.homeDirectory}/.local/share/agent-plugins/dotfiles"
        CLAUDE_CONFIG_DIR="${config.home.homeDirectory}/.claude" \
          ${config.claude.unwrappedPackage}/bin/claude plugin install dotfiles@dotagents
        CLAUDE_CONFIG_DIR="${config.home.homeDirectory}/.claude" \
          ${config.claude.unwrappedPackage}/bin/claude plugin update dotfiles@dotagents
      '';
}
