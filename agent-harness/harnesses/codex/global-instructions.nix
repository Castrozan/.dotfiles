{ config, ... }:
{
  home.file.".codex/AGENTS.md".source = "${config.agentPlugins.bundle}/plugin/native/codex/AGENTS.md";
}
