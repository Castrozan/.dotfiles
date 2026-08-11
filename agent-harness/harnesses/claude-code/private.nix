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

  # Files Claude reads straight out of ~/.claude on this machine alone, such as the
  # employer daily report template a plugin command renders into. The same directory
  # carries nix modules other harness pieces import, so only non-nix regular files
  # become home files.
  machineClaudeDir = ../../../private-configuration/machines + "/${hostname}/claude";

  machineClaudeFiles =
    if builtins.pathExists machineClaudeDir then
      builtins.attrNames (
        lib.filterAttrs (fileName: fileType: fileType == "regular" && !lib.hasSuffix ".nix" fileName) (
          builtins.readDir machineClaudeDir
        )
      )
    else
      [ ];

  machineClaudeSymlinks = builtins.listToAttrs (
    map (filename: {
      name = ".claude/${filename}";
      value = {
        source = "${machineClaudeDir}/${filename}";
      };
    }) machineClaudeFiles
  );
in
{
  home.file = privateAgentSymlinks // machineClaudeSymlinks;
}
