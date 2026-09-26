{ config, ... }:
{
  home.file.".config/opencode/AGENTS.md".source =
    "${config.agentPlugins.bundle}/plugin/native/opencode/AGENTS.md";
}
