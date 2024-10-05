# This is a NixOS module that installs a tmux screensaver script
{ pkgs, ... }:

let
  code = builtins.readFile /home/zanoni/.dotfiles/shell/configs/screensaver.sh;
  screensaver = pkgs.writeShellScriptBin "screensaver" = ''${code}'';
in
{
  environment.systemPackages = [ screensaver ];
}


