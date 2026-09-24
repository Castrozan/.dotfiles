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
        ${config.claude.unwrappedPackage}/bin/claude plugin marketplace add "${config.home.homeDirectory}/.local/share/agent-plugins/dotfiles"
        ${config.claude.unwrappedPackage}/bin/claude plugin install dotfiles@dotagents
        ${config.claude.unwrappedPackage}/bin/claude plugin update dotfiles@dotagents
      '';
}
