{ lib, hostname, ... }:
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

  machineClaudeHomeFilesDir = ../../../private-configuration/machines + "/${hostname}/claude";

  machineClaudeHomeFiles =
    if builtins.pathExists machineClaudeHomeFilesDir then
      builtins.attrNames (
        lib.filterAttrs (fileName: fileType: fileType == "regular" && !lib.hasSuffix ".nix" fileName) (
          builtins.readDir machineClaudeHomeFilesDir
        )
      )
    else
      [ ];

  machineClaudeHomeFileSymlinks = builtins.listToAttrs (
    map (filename: {
      name = ".claude/${filename}";
      value = {
        source = "${machineClaudeHomeFilesDir}/${filename}";
      };
    }) machineClaudeHomeFiles
  );
in
{
  home.file = privateAgentSymlinks // machineClaudeHomeFileSymlinks;
}
