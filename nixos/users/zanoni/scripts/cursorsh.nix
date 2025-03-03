{ pkgs, ... }:
let
  script = builtins.readFile ../../../../bin/cursorsh;
in
let
  cursorsh = pkgs.writeShellScriptBin "cursorsh" ''
    ${script}
  '';
in
{
  environment.systemPackages = [ cursorsh ];
}
