{ pkgs, ... }:
let
  script = builtins.readFile ../../bin/tmux-resurrect;
in
{
  home.packages = [
    (pkgs.writeShellScriptBin "tmux-resurrect" script)
  ];
}
