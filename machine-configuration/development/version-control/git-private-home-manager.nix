{
  lib,
  hostname,
  ...
}:
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
