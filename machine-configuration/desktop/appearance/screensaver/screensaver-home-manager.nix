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
  precomputeLoopSources = pkgs.runCommand "precompute-loop-sources" { } ''
    mkdir -p "$out"
    cp ${./scripts/precompute_loop.py} "$out/precompute_loop.py"
    cp ${./scripts/precompute_loop_terminal.py} "$out/precompute_loop_terminal.py"
  '';
  precomputeLoop = pkgs.writeShellScriptBin "precompute-loop" ''
    exec ${pkgs.python312}/bin/python3 ${precomputeLoopSources}/precompute_loop.py "$@"
  '';
  equationArtPython = pkgs.python312.withPackages (pythonPackages: [ pythonPackages.numpy ]);
in
{
  imports = [ ./ambient-canvas/ambient-canvas-home-manager.nix ];

  home.packages = [
    precomputeLoop
    (mkScreensaverPythonScriptWith "equation-art" ./scripts/equation_art.py equationArtPython)
  ]
  ++ lib.optional pkgs.stdenv.hostPlatform.isLinux (
    mkScreensaverPythonScript "herdr-screensaver" ./scripts/launch_herdr_screensaver.py
  );
}
