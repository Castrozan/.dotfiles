{ lib, ... }:
let
  privateConfigDir = ../../../private-configuration/claude;
  agentsDir = privateConfigDir + "/agents";

  agentsDirExists = builtins.pathExists agentsDir;

  privateAgentFiles =
    if agentsDirExists then
      builtins.filter (name: lib.hasSuffix ".md" name && name != ".gitkeep") (
        builtins.attrNames (builtins.readDir agentsDir)
      )
    else
      [ ];

  privateAgentSymlinks = builtins.listToAttrs (
    map (filename: {
      name = ".claude/agents/${filename}";
      value = {
        source = "${agentsDir}/${filename}";
      };
    }) privateAgentFiles
  );
in
{
  home.file = lib.mkIf agentsDirExists privateAgentSymlinks;
}
