{ pkgs, lib, ... }:
let
  privateConfigDir = ../../../private-configuration/agent-harness/claude;
  agentsDir = privateConfigDir + "/agents";

  agentsDirExists = builtins.pathExists agentsDir;

  privateAgentDefinitions =
    if agentsDirExists then
      import ./agents/translate-claude-agent-definitions.nix {
        inherit pkgs;
        derivationName = "opencode-private-agent-definitions";
        claudeAgentDefinitionsDirectory = agentsDir;
      }
    else
      null;

  privateAgentFileNames =
    if agentsDirExists then
      builtins.filter (fileName: lib.hasSuffix ".md" fileName) (
        builtins.attrNames (builtins.readDir agentsDir)
      )
    else
      [ ];

  privateAgentEntries = builtins.listToAttrs (
    map (fileName: {
      name = ".config/opencode/agent/${fileName}";
      value = {
        source = "${privateAgentDefinitions}/${fileName}";
      };
    }) privateAgentFileNames
  );

in
{
  home.file = privateAgentEntries;
}
