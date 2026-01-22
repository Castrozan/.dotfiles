# Script to open Ksnip with clipboard image for annotation
{ pkgs, ... }:
let
  script = builtins.readFile ../../bin/ksnip-annotate;

  ksnip-annotate = pkgs.writeShellScriptBin "ksnip-annotate" ''
    ${script}
  '';
in
{
  home.packages = [ ksnip-annotate ];
}
