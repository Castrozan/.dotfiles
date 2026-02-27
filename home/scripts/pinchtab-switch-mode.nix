{ pkgs, ... }:
let
  script = builtins.readFile ../../bin/pinchtab-switch-mode;

  pinchtab-switch-mode = pkgs.writeShellScriptBin "pinchtab-switch-mode" ''
    ${script}
  '';
in
{
  home.packages = [ pinchtab-switch-mode ];
}
