{ pkgs, ... }:
let
  script = builtins.readFile ../../bin/volume;

  volume = pkgs.writeShellScriptBin "volume" ''
    export PATH="${pkgs.pulseaudio}/bin:${pkgs.libnotify}/bin:$PATH"
    ${script}
  '';
in
{
  home.packages = [ volume ];
}
