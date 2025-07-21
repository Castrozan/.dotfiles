# All Zanoni's Home Manager Configuration
{
  imports = [
    ../../home/core.nix
    ./pkgs.nix

    # ../../home/hyprland
    ../../home/modules/gnome
    ../../home/modules/kitty.nix
    ../../home/modules/tmux.nix
    ../../home/modules/lazygit.nix
    # ../../home/packages
    # ../../home/vscode
  ];
}
