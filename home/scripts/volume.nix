{ pkgs, config, ... }:
let
  script = builtins.readFile ../../bin/volume;

  volume = pkgs.writeShellScriptBin "volume" ''
    export PATH="${pkgs.pulseaudio}/bin:${config.home.profileDirectory}/bin:$PATH"
    ${script}
  '';
in
{
  home.packages = [ volume ];
}
