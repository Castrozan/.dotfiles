{
  pkgs,
  config,
  ...
}:
let
  mkAudioPythonScriptWithDeps =
    name: file: runtimeDeps:
    let
      pythonSource = pkgs.writeText "${name}-source.py" (builtins.readFile file);
      allDeps = runtimeDeps ++ [ config.home.profileDirectory ];
    in
    pkgs.writeShellScriptBin name ''
      export PATH="${pkgs.lib.makeBinPath allDeps}:$PATH"
      exec ${pkgs.python312}/bin/python3 ${pythonSource} "$@"
    '';
in
{
  home.packages = [
    (mkAudioPythonScriptWithDeps "volume" ./scripts/volume.py [
      pkgs.pulseaudio
    ])
    (mkAudioPythonScriptWithDeps "audio-output-switch" ./scripts/audio_output_switch.py [
      pkgs.pulseaudio
      pkgs.libnotify
    ])
  ];
}
