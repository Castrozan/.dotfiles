# Zanoni's Home Manager Configuration
{
  imports = [
    ../../home/core.nix

    ./home/git.nix

    ../../home/modules/hyprland
    ../../home/modules/gnome
    ../../home/modules/kitty.nix
    ../../home/modules/vscode
    ../../home/modules/common.nix
    ../../home/modules/bash.nix
    ../../home/modules/pkgs.nix
    ../../home/modules/neovim.nix
    ../../home/modules/tmux.nix
    ../../home/modules/fuzzel.nix
    ../../home/modules/playwright.nix
    ../../home/modules/vesktop.nix
    ../../home/modules/lazygit.nix
  ];
}
