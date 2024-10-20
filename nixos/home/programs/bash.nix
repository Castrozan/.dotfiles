{ pkgs, ... }:

let
  bashrc = builtins.readFile ../../../.bashrc;
in
{
  # Global Bash configuration
  home.file.".bashrc".text = bashrc;
}
