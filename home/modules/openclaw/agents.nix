{ lib, ... }:
let
  openclawAgentDir = ../../../agents/openclaw;

  openclawAgentFiles = builtins.filter (name: lib.hasSuffix ".md" name) (
    builtins.attrNames (builtins.readDir openclawAgentDir)
  );

  openclawAgentSymlinks = builtins.listToAttrs (
    map (filename: {
      name = "clawd/.nix/${filename}";
      value = {
        source = openclawAgentDir + "/${filename}";
      };
    }) openclawAgentFiles
  );
in
{
  home.file = openclawAgentSymlinks;
}
