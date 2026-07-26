{ pkgs, ... }:
let
  rilCli = import ../../../agents/skills/ril/install { inherit pkgs; };
in
{
  home.packages = rilCli.packages;
}
