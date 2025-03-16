{ config, pkgs, lib, inputs, ... }:

{
  imports = [
    ./browsers.nix
    ./claude-desktop.nix
    ./common.nix
    ./git.nix
    ./bash.nix
    ./pkgs.nix
    ./neovim.nix
    ./tmux.nix
    ./vscode.nix
    ./hyprland.nix
    ./fuzzel.nix
    # ./media.nix
    # ./xdg.nix
  ];
}
