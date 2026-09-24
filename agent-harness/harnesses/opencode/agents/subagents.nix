{ config, ... }:
{
  imports = [ ../../../agent-instructions/production-plugin/home-manager.nix ];
  home.file.".config/opencode/agent" = {
    source = "${config.agentPlugins.bundle}/plugin/native/opencode/agents";
    recursive = true;
  };
}
