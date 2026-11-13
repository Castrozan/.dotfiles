{ pkgs, ... }:
let
  ccusage = import ./ccusage-package.nix { inherit pkgs; };
in
{
  home.packages = [ ccusage ];
}
