{
  lib,
  hostname,
  ...
}:
# hostname is required from extraSpecialArgs. Threaded by:
#   flake/outputs.nix (homeConfigurations), flake/darwin-configurations.nix (darwin).
# Adds private-config/machines/<hostname>/git-user.nix when that file exists.
let
  privateConfigRoot = ../../../private-config;
  privateConfigExists = builtins.pathExists privateConfigRoot;
  privateGitUserPath = "${toString privateConfigRoot}/machines/${hostname}/git-user.nix";
  privateGitUserExists = privateConfigExists && builtins.pathExists privateGitUserPath;
in
{
  imports = [
    ./git.nix
  ]
  ++ lib.optionals privateGitUserExists [
    privateGitUserPath
  ];
}
