{ pkgs, ... }:

let
  bashrc = builtins.readFile ../.bashrc;
in
{
  # Global Bash configuration
  environment.etc."bashrc".text = bashrc;
}
