{ pkgs, ... }:
let
  mkTerminalPythonScript =
    name: file:
    let
      pythonSource = pkgs.writeText "${name}-source.py" (builtins.readFile file);
    in
    pkgs.writeShellScriptBin name ''
      exec ${pkgs.python312}/bin/python3 ${pythonSource} "$@"
    '';
in
{
  home.packages = [
    (mkTerminalPythonScript "herdr-screensaver" ./scripts/launch_herdr_screensaver.py)
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
  ];
}
