# Script to toggle btop pane in tmux
{ pkgs, ... }:
let
  script = builtins.readFile ../../bin/tmux-btop-toggle;

  tmux-btop-toggle = pkgs.writeShellScriptBin "tmux-btop-toggle" ''
    ${script}
  '';
in
{
  home.packages = [ tmux-btop-toggle ];
}

