{ pkgs, config, ... }:
let
  script = builtins.readFile ../../bin/audio-output-switch;

  audioOutputSwitch = pkgs.writeShellScriptBin "audio-output-switch" ''
    export PATH="${pkgs.pulseaudio}/bin:${pkgs.libnotify}/bin:${config.home.profileDirectory}/bin:$PATH"
    ${script}
  '';
in
{
  home.packages = [ audioOutputSwitch ];
}
