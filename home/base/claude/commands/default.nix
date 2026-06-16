{ lib, ... }:
let
  publicCommandsDirectory = ../../../../agents/commands;

  commandMarkdownFileNames =
    if builtins.pathExists publicCommandsDirectory then
      builtins.filter (fileName: lib.hasSuffix ".md" fileName) (
        builtins.attrNames (builtins.readDir publicCommandsDirectory)
      )
    else
      [ ];

  publicCommandSymlinks = builtins.listToAttrs (
    map (fileName: {
      name = ".claude/commands/${fileName}";
      value.source = publicCommandsDirectory + "/${fileName}";
    }) commandMarkdownFileNames
  );
in
{
  home.file = publicCommandSymlinks;
}
