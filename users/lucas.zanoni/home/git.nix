{
  lib,
  hostname,
  ...
}:
let
  privateConfigRoot = ../../../private-config;
  privateConfigExists = builtins.pathExists privateConfigRoot;
  privateGitUserPath = "${toString privateConfigRoot}/machines/${hostname}/git-user.nix";
  privateGitUserExists = privateConfigExists && builtins.pathExists privateGitUserPath;
in
{
  imports = [
    ../../../home/base/dev/git.nix
  ]
  ++ lib.optionals privateGitUserExists [
    privateGitUserPath
  ];
}
