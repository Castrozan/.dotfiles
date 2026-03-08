{ pkgs, ... }:
{
  home.packages = [
    (pkgs.writeShellScriptBin "tmux-lazygit-toggle" (builtins.readFile ./scripts/tmux-lazygit-toggle))
    (pkgs.writeShellScriptBin "tmux-btop-toggle" (builtins.readFile ./scripts/tmux-btop-toggle))
    (pkgs.writeShellScriptBin "tmux-editor-toggle" (builtins.readFile ./scripts/tmux-editor-toggle))
    (pkgs.writeShellScriptBin "tmux-resurrect" (builtins.readFile ./scripts/tmux-resurrect))
    (pkgs.writeShellScriptBin "tmux-session-chooser" (builtins.readFile ./scripts/tmux-session-chooser))
    (pkgs.writeShellScriptBin "set-random-bg-kitty" (builtins.readFile ./scripts/set-random-bg-kitty))
  ];
}
