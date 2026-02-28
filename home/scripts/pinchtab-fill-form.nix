{ pkgs, ... }:
let
  script = builtins.readFile ../../bin/pinchtab-fill-form;

  pinchtab-fill-form = pkgs.writeShellScriptBin "pinchtab-fill-form" ''
    ${script}
  '';
in
{
  home.packages = [ pinchtab-fill-form ];
}
