{ lib, ... }:
let
  sharedSubagentDir = ../../../agents/subagent;

  subagentFiles = builtins.filter (name: lib.hasSuffix ".md" name) (
    builtins.attrNames (builtins.readDir sharedSubagentDir)
  );

  subagentSymlinks = builtins.listToAttrs (
    map (filename: {
      name = "clawd/.nix/subagents/${filename}";
      value = {
        source = sharedSubagentDir + "/${filename}";
      };
    }) subagentFiles
  );
in
{
  home.file = subagentSymlinks;
}
