{
  pkgs,
  lib,
  mkEvalCheck,
  cfg,
}:
{
  claude-avatar-plugin-registration =
    mkEvalCheck "claude-avatar-plugin-registration"
      (
        toString cfg.home.file.".local/share/agent-plugins/avatar".source
        == toString cfg.agentPlugins.avatarPlugin
        && lib.hasInfix "plugin marketplace add \"${cfg.home.homeDirectory}/.local/share/agent-plugins/avatar\"" cfg.home.activation.installAvatarClaudePlugin.data
        && lib.hasInfix "plugin install avatar@avatar" cfg.home.activation.installAvatarClaudePlugin.data
      )
      "Claude must register the pinned avatar plugin directory as the avatar marketplace and install avatar@avatar from it, so the skill and the runtime move with one pin";

  claude-avatar-plugin-enabled-in-settings =
    pkgs.runCommand "claude-avatar-plugin-enabled-in-settings" { }
      ''
        ${pkgs.jq}/bin/jq -e '.enabledPlugins["avatar@avatar"] == true and .enabledPlugins["dotfiles@dotagents"] == true' \
          ${cfg.home.file.".claude/settings.json.nix-source".source} > /dev/null
        touch "$out"
      '';
}
