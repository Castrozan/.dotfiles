{ pkgs, ... }:
let
  script = builtins.readFile ../../bin/tmux-refresh-hyprland-env;
in
{
  home.packages = [
    (pkgs.writeShellScriptBin "tmux-refresh-hyprland-env" script)
  ];
}
