{ pkgs, ... }:
let
  todoCli = import ./default.nix { inherit pkgs; };
in
{
  home.packages = todoCli.packages;
}
