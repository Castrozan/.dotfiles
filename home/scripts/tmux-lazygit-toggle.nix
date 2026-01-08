# Script to toggle lazygit pane in tmux
{ pkgs, ... }:
let
  script = builtins.readFile ../../bin/tmux-lazygit-toggle;
in
let
  tmux-lazygit-toggle = pkgs.writeShellScriptBin "tmux-lazygit-toggle" ''
    ${script}
  '';
in
{
  home.packages = [ tmux-lazygit-toggle ];
}

