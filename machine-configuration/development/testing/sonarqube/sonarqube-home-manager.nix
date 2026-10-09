{ pkgs, ... }:
let
  tools = import ./sonarqube-tools.nix { inherit pkgs; };
in
{
  home.packages = [
    tools.cli
    tools.configure
    tools.scanner
  ];
}
