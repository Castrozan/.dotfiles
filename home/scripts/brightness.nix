{ pkgs, ... }:
let
  script = builtins.readFile ../../bin/brightness;

  brightness = pkgs.writeShellScriptBin "brightness" ''
    export PATH="${pkgs.brightnessctl}/bin:${pkgs.libnotify}/bin:$PATH"
    ${script}
  '';
in
{
  home.packages = [ brightness ];
}
