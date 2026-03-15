{ pkgs, ... }:
let
  agentBrowserPackage = pkgs.callPackage ./agent-browser-package.nix { };
in
{
  home.packages = [
    agentBrowserPackage
  ];
}
