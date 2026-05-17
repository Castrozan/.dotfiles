{ pkgs, ... }:
{
  home.packages = [
    (pkgs.writeShellScriptBin "tmux-pane-toggle" (builtins.readFile ./scripts/tmux-pane-toggle))
    (pkgs.writeShellScriptBin "tmux-resurrect" (builtins.readFile ./scripts/tmux-resurrect))
    (pkgs.writeShellScriptBin "tmux-session-chooser" (builtins.readFile ./scripts/tmux-session-chooser))
    (pkgs.writeShellScriptBin "set-random-bg-kitty" (builtins.readFile ./scripts/set-random-bg-kitty))
  ];
}
