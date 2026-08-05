{ lib, ... }:
let
  publicCommandsDirectory = ../../../agent-harness/agent-instructions/commands;

  commandMarkdownFileNames =
    if builtins.pathExists publicCommandsDirectory then
      builtins.filter (fileName: lib.hasSuffix ".md" fileName) (
        builtins.attrNames (builtins.readDir publicCommandsDirectory)
      )
    else
      [ ];

  publicCommandSymlinks = builtins.listToAttrs (
    map (fileName: {
      name = ".config/opencode/command/${fileName}";
      value.source = publicCommandsDirectory + "/${fileName}";
    }) commandMarkdownFileNames
  );
in
{
  home.file = publicCommandSymlinks;
}
