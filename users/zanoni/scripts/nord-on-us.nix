{ pkgs, ... }:
let
  script = builtins.readFile ../../../bin/nord-on-us;
in
let
  nord-on-us = pkgs.writeShellScriptBin "nord-on-us" ''
    ${script}
  '';
in
{
  environment.systemPackages = [ nord-on-us ];
}
