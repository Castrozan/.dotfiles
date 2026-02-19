{ pkgs, ... }:
let
  script = builtins.readFile ../../bin/pinchtab-ensure-running;

  pinchtab-ensure-running = pkgs.writeShellScriptBin "pinchtab-ensure-running" ''
    ${script}
  '';
in
{
  home.packages = [ pinchtab-ensure-running ];
}
