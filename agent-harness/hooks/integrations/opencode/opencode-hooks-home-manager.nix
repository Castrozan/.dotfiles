{ config, ... }:
{
  imports = [ ../../../agent-instructions/production-plugin/home-manager.nix ];
  home.file.".config/opencode/plugins/opencode-hook-bridge.js".source =
    "${config.agentPlugins.bundle}/plugin/native/opencode/hooks/opencode-hook-bridge.js";
}
