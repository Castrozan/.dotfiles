{ lib, ... }:
let
  privateConfigDir = ../../../private-config/claude;
  agentsDir = privateConfigDir + "/agents";
  commandsDir = privateConfigDir + "/commands";

  agentsDirExists = builtins.pathExists agentsDir;
  commandsDirExists = builtins.pathExists commandsDir;

  privateAgentFiles =
    if agentsDirExists then
      builtins.filter (name: lib.hasSuffix ".md" name && name != ".gitkeep") (
        builtins.attrNames (builtins.readDir agentsDir)
      )
    else
      [ ];

  privateCommandFiles =
    if commandsDirExists then
      builtins.filter (name: lib.hasSuffix ".md" name && name != ".gitkeep") (
        builtins.attrNames (builtins.readDir commandsDir)
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

  privateCommandSymlinks = builtins.listToAttrs (
    map (filename: {
      name = ".claude/commands/${filename}";
      value = {
        source = "${commandsDir}/${filename}";
      };
    }) privateCommandFiles
  );
in
{
  home.file = lib.mkIf (agentsDirExists || commandsDirExists) (
    privateAgentSymlinks // privateCommandSymlinks
  );
}
