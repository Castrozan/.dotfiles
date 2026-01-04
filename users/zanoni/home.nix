# Zanoni's Home Manager Configuration
{
  imports = [
    ./home/git.nix
    ./home/session-vars.nix

    ../../home/core.nix
    ../../home/scripts
    ../../home/modules/hyprland
    ../../home/modules/gnome
    ../../home/modules/kitty.nix
    ../../home/modules/fish.nix
    ../../home/modules/vscode
    # ../../home/modules/common.nix
    ../../home/modules/bash.nix
    ../../home/modules/pkgs.nix
    ../../home/modules/neovim.nix
    ../../home/modules/tmux.nix
    ../../home/modules/fuzzel.nix
    ../../home/modules/playwright.nix
    ../../home/modules/cursor
    ../../home/modules/vesktop.nix
    ../../home/modules/lazygit.nix
    ../../home/modules/flameshot.nix
    ../../home/modules/vial.nix
    ../../home/modules/cbonsai.nix
    ../../home/modules/cmatrix.nix
    ../../home/modules/install-nothing.nix
  ];
}
