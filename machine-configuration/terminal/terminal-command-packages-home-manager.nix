{ pkgs, ... }:
{
  home.packages = [
    (pkgs.writeShellScriptBin "tmux-pane-toggle" (
      builtins.readFile ./multiplexer/tmux/scripts/tmux-pane-toggle
    ))
    (pkgs.writeShellScriptBin "tmux-restore-pane-after-toggle" (
      builtins.readFile ./multiplexer/tmux/scripts/tmux-restore-pane-after-toggle
    ))
    (pkgs.writeShellScriptBin "tmux-wait-pane-resize" (
      builtins.readFile ./multiplexer/tmux/scripts/tmux-wait-pane-resize
    ))
    (pkgs.writeShellScriptBin "tmux-binding-run" (
      builtins.readFile ./multiplexer/tmux/scripts/tmux-binding-run
    ))
    (pkgs.writeShellScriptBin "tmux-window-to-new-session" (
      builtins.readFile ./multiplexer/tmux/scripts/tmux-window-to-new-session
    ))
    (pkgs.writeShellScriptBin "tmux-resurrect" (
      builtins.readFile ./multiplexer/tmux/scripts/tmux-resurrect
    ))
    (pkgs.writeShellScriptBin "tmux-session-chooser" (
      builtins.readFile ./multiplexer/tmux/scripts/tmux-session-chooser
    ))
    (pkgs.writeShellScriptBin "set-random-bg-kitty" (
      builtins.readFile ./emulators/kitty/scripts/set-random-bg-kitty
    ))
    (pkgs.writeShellScriptBin "nix" (
      builtins.readFile ./shell/bash/scripts/nix-memory-capped-wrapper.sh
    ))
  ];
}
