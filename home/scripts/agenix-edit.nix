{ pkgs, ... }:
let
  script = builtins.readFile ../../bin/agenix-edit;
in
{
  home.packages = [
    (pkgs.writeShellScriptBin "agenix-edit" script)
  ];
}
