{ pkgs, ... }:
let
  script = builtins.readFile ../../bin/tmux-restore;
in
let
  tmux-restore = pkgs.writeShellScriptBin "tmux-restore" ''
    ${script}
  '';
in
{
  home.packages = [ tmux-restore ];
}

