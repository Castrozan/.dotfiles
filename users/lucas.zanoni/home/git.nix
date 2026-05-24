{ lib, ... }:
let
  workpcPrivateConfigDirectory = ../../../private-config/machines/workpc;
  workpcPrivateConfigExists = builtins.pathExists workpcPrivateConfigDirectory;
in
{
  imports = [
    ../../../home/modules/dev/git.nix
  ]
  ++ lib.optionals workpcPrivateConfigExists [
    "${workpcPrivateConfigDirectory}/git-user.nix"
  ];
}
