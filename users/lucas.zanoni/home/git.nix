{ lib, ... }:
let
  privateConfigRoot = ../../../private-config;
  workpcPrivateConfigExists = builtins.pathExists privateConfigRoot;
in
{
  imports = [
    ../../../home/base/dev/git.nix
  ]
  ++ lib.optionals workpcPrivateConfigExists [
    "${privateConfigRoot}/machines/workpc/git-user.nix"
  ];
}
