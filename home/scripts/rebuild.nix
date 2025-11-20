{ pkgs, ... }:
let
  script = builtins.readFile ../../bin/rebuild;
in
let
  rebuild = pkgs.writeShellScriptBin "rebuild" ''
    ${script}
  '';
in
{
  home.packages = [ rebuild ];
}
