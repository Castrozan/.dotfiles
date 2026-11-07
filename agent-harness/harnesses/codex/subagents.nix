{ config, ... }:
{
  home.file.".codex/agents" = {
    source = "${config.agentPlugins.bundle}/plugin/native/codex/agents";
    recursive = true;
  };
}
