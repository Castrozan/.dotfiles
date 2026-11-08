{ pkgs, ... }:
{
  home.packages = [ (import ./orchestrator-package.nix { inherit pkgs; }) ];
}
