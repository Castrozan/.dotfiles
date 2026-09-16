{ pkgs, ... }:
let
  rilCli = import ./default.nix { inherit pkgs; };
in
{
  home.packages = rilCli.packages;
}
