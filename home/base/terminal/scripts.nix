{ pkgs, ... }:
{
  home.packages = [
    (pkgs.writeShellScriptBin "tmux-pane-toggle" (builtins.readFile ./scripts/tmux-pane-toggle))
    (pkgs.writeShellScriptBin "tmux-restore-pane-after-toggle" (
      builtins.readFile ./scripts/tmux-restore-pane-after-toggle
    ))
    (pkgs.writeShellScriptBin "tmux-wait-pane-resize" (
      builtins.readFile ./scripts/tmux-wait-pane-resize
    ))
    (pkgs.writeShellScriptBin "tmux-binding-run" (builtins.readFile ./scripts/tmux-binding-run))
    (pkgs.writeShellScriptBin "tmux-resurrect" (builtins.readFile ./scripts/tmux-resurrect))
    (pkgs.writeShellScriptBin "tmux-session-chooser" (builtins.readFile ./scripts/tmux-session-chooser))
    (pkgs.writeShellScriptBin "set-random-bg-kitty" (builtins.readFile ./scripts/set-random-bg-kitty))
  ];
}
