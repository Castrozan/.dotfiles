{ pkgs, config, ... }:
let
  script = builtins.readFile ../../bin/brightness;

  brightness = pkgs.writeShellScriptBin "brightness" ''
    export PATH="${pkgs.brightnessctl}/bin:${config.home.profileDirectory}/bin:$PATH"
    ${script}
  '';
in
{
  home.packages = [ brightness ];
}
