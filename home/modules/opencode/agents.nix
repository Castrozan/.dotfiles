{ lib, ... }:
let
  inherit (import ./lib.nix) colorNameToHex processAgentFile;

  agentsDir = ../../../agents/subagent;

  agentFiles = builtins.filter (name: lib.hasSuffix ".md" name) (
    builtins.attrNames (builtins.readDir agentsDir)
  );

  agentEntries = builtins.listToAttrs (
    map (filename: {
      name = ".config/opencode/agents/${filename}";
      value = {
        text = processAgentFile colorNameToHex (builtins.readFile (agentsDir + "/${filename}"));
      };
    }) agentFiles
  );
in
{
  home.file = agentEntries;
}
