{ pkgs, ... }:
let
  opencodeAgentDefinitions = import ./translate-claude-agent-definitions.nix {
    inherit pkgs;
    derivationName = "opencode-agent-definitions";
    claudeAgentDefinitionsDirectory = ../../../agents/subagents;
  };
in
{
  home.file.".config/opencode/agent" = {
    source = opencodeAgentDefinitions;
    recursive = true;
  };
}
