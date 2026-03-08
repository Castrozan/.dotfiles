{ pkgs, config, ... }:
{
  home.packages = [
    (pkgs.writeShellScriptBin "volume" ''
      export PATH="${pkgs.pulseaudio}/bin:${config.home.profileDirectory}/bin:$PATH"
      ${builtins.readFile ./scripts/volume}
    '')
    (pkgs.writeShellScriptBin "audio-output-switch" ''
      export PATH="${pkgs.pulseaudio}/bin:${pkgs.libnotify}/bin:${config.home.profileDirectory}/bin:$PATH"
      ${builtins.readFile ./scripts/audio-output-switch}
    '')
  ];
}
