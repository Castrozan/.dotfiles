{ pkgs, lib, ... }:
let
  mkTerminalPythonScriptWith =
    name: file: pythonInterpreter:
    let
      pythonSource = pkgs.writeText "${name}-source.py" (builtins.readFile file);
    in
    pkgs.writeShellScriptBin name ''
      exec ${pythonInterpreter}/bin/python3 ${pythonSource} "$@"
    '';
  mkTerminalPythonScript = name: file: mkTerminalPythonScriptWith name file pkgs.python312;
  equationArtPython = pkgs.python312.withPackages (pythonPackages: [ pythonPackages.numpy ]);
in
{
  home.packages = [
    (mkTerminalPythonScript "precompute-loop" ./scripts/precompute_loop.py)
    (mkTerminalPythonScriptWith "equation-art" ./scripts/equation_art.py equationArtPython)
    (pkgs.writeShellScriptBin "tmux-pane-toggle" (builtins.readFile ./scripts/tmux-pane-toggle))
    (pkgs.writeShellScriptBin "tmux-restore-pane-after-toggle" (
      builtins.readFile ./scripts/tmux-restore-pane-after-toggle
    ))
    (pkgs.writeShellScriptBin "tmux-wait-pane-resize" (
      builtins.readFile ./scripts/tmux-wait-pane-resize
    ))
    (pkgs.writeShellScriptBin "tmux-binding-run" (builtins.readFile ./scripts/tmux-binding-run))
    (pkgs.writeShellScriptBin "tmux-window-to-new-session" (
      builtins.readFile ./scripts/tmux-window-to-new-session
    ))
    (pkgs.writeShellScriptBin "tmux-resurrect" (builtins.readFile ./scripts/tmux-resurrect))
    (pkgs.writeShellScriptBin "tmux-session-chooser" (builtins.readFile ./scripts/tmux-session-chooser))
    (pkgs.writeShellScriptBin "set-random-bg-kitty" (builtins.readFile ./scripts/set-random-bg-kitty))
    (pkgs.writeShellScriptBin "nix" (builtins.readFile ./scripts/nix-memory-capped-wrapper.sh))
  ]
  ++ lib.optional pkgs.stdenv.hostPlatform.isLinux (
    mkTerminalPythonScript "herdr-screensaver" ./scripts/launch_herdr_screensaver.py
  );
}
