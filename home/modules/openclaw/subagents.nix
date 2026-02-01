{ lib, ... }:
let
  sharedSubagentDir = ../../../agents/subagent;

  subagentFiles = builtins.filter (name: lib.hasSuffix ".md" name) (
    builtins.attrNames (builtins.readDir sharedSubagentDir)
  );

  subagentEntries = builtins.listToAttrs (
    map (filename: {
      name = "clawd/subagents/${filename}";
      value.text = builtins.readFile (sharedSubagentDir + "/${filename}");
    }) subagentFiles
  );
in
{
  home.file = subagentEntries;
}
