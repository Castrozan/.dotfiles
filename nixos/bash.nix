{ pkgs, ... }:

let
  bashrc = builtins.readFile /home/zanoni/.dotfiles/.bashrc;
in
{
  # Global Bash configuration
  environment.etc."bashrc".text = bashrc;
}
