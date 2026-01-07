# Script to trigger greatshot with capture selection
{ pkgs, ... }:
let
  script = builtins.readFile ../../bin/greatshot-capture;
in
let
  greatshot-capture = pkgs.writeShellScriptBin "greatshot-capture" ''
    ${script}
  '';
in
{
  home.packages = [ greatshot-capture ];
}

