{ config, ... }:
{
  imports = [ ../../../agent-instructions/production-plugin/home-manager.nix ];
  home.file.".config/opencode/plugins/rulesync-hooks.js".source =
    "${config.agentPlugins.bundle}/plugin/native/opencode/hooks";
}
