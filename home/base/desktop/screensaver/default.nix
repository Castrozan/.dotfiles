{
  pkgs,
  lib,
  ...
}:
let
  mkScreensaverPythonScriptWith =
    name: file: pythonInterpreter:
    let
      pythonSource = pkgs.writeText "${name}-source.py" (builtins.readFile file);
    in
    pkgs.writeShellScriptBin name ''
      exec ${pythonInterpreter}/bin/python3 ${pythonSource} "$@"
    '';
  mkScreensaverPythonScript = name: file: mkScreensaverPythonScriptWith name file pkgs.python312;
  equationArtPython = pkgs.python312.withPackages (pythonPackages: [ pythonPackages.numpy ]);
in
{
  imports = [ ./ambient-canvas ];

  home.packages = [
    (mkScreensaverPythonScript "precompute-loop" ./scripts/precompute_loop.py)
    (mkScreensaverPythonScriptWith "equation-art" ./scripts/equation_art.py equationArtPython)
  ]
  ++ lib.optional pkgs.stdenv.hostPlatform.isLinux (
    mkScreensaverPythonScript "herdr-screensaver" ./scripts/launch_herdr_screensaver.py
  );
}
