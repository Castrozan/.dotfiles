{ lib, ... }:
let
  agentsDir = ../../../agents/subagent;

  # Get all .md files from the subagent directory
  agentFiles = builtins.filter
    (name: lib.hasSuffix ".md" name)
    (builtins.attrNames (builtins.readDir agentsDir));

  # Create home.file entries for each agent
  agentSymlinks = builtins.listToAttrs (map
    (filename: {
      name = ".claude/agents/${filename}";
      value = { source = agentsDir + "/${filename}"; };
    })
    agentFiles);
in
{
  home.file = agentSymlinks;
}
