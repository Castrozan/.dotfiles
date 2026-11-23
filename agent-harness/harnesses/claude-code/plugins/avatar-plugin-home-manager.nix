{ config, lib, ... }:
{
  imports = [ ../../../agent-instructions/production-plugin/home-manager.nix ];

  home.activation.installAvatarClaudePlugin =
    lib.hm.dag.entryAfter
      [
        "linkGeneration"
        "seedClaudeSettingsAsMutableFile"
      ]
      ''
        CLAUDE_CONFIG_DIR="${config.home.homeDirectory}/.claude" \
          ${config.claude.unwrappedPackage}/bin/claude plugin marketplace add "${config.home.homeDirectory}/.local/share/agent-plugins/avatar"
        CLAUDE_CONFIG_DIR="${config.home.homeDirectory}/.claude" \
          ${config.claude.unwrappedPackage}/bin/claude plugin install avatar@avatar
      '';
}
