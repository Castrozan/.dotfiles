{ pkgs, ... }:
{
  home.packages = [ (import ./speech-package.nix { inherit pkgs; }) ];
}
