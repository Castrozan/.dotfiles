{ pkgs, lib, ... }:
let
  source = import ../. {
    inherit pkgs lib;
    hostname = "test";
    homeDirectory = "/home/test";
    chromePackage = pkgs.google-chrome;
    isDarwin = false;
  };
  bundle = (import ../../../plugin-distribution { inherit pkgs; }).buildPlugin { inherit source; };
in
{
  production-plugin-artifact-preservation =
    pkgs.runCommand "production-plugin-artifact-preservation" { }
      ''
        ${pkgs.python312}/bin/python3 ${./verify-production-bundle.py} ${bundle}
        touch "$out"
      '';
}
