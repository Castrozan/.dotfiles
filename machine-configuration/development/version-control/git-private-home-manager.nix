{
  lib,
  hostname,
  ...
}:
# Adds private-configuration/machines/<hostname>/git-user.nix when that file exists.
let
  privateConfigRoot = ../../../private-configuration;
  privateConfigExists = builtins.pathExists privateConfigRoot;
  privateGitUserPath = "${toString privateConfigRoot}/machines/${hostname}/git-user.nix";
  privateGitUserExists = privateConfigExists && builtins.pathExists privateGitUserPath;
in
{
  imports = [
    ./git-home-manager.nix
  ]
  ++ lib.optionals privateGitUserExists [
    privateGitUserPath
  ];
}
