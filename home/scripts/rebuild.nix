{ pkgs, ... }:
let
  script = builtins.readFile ../../bin/rebuild;

  rebuild = pkgs.writeShellScriptBin "rebuild" ''
    ${script}
  '';
in
{
  home.packages = [ rebuild ];
}
