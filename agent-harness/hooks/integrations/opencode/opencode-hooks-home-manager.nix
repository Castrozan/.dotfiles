{ config, ... }:
{
  imports = [ ../../../agent-instructions/production-plugin/home-manager.nix ];
  home.file.".config/opencode/plugins/dotfiles-hook-bridge".source =
    "${config.agentPlugins.bundle}/plugin/native/opencode/hooks";
}
