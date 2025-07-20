# Zanoni's Home Manager Configuration
{
  username,
  specialArgs,
  ...
}:
{
  home-manager.nixosModules.home-manager = {
    home-manager.useGlobalPkgs = true;
    home-manager.useUserPackages = true;
    home-manager.backupFileExtension = "backup";
    home-manager.extraSpecialArgs = specialArgs;
    home-manager.users.${username} = {
      imports = [
        ../../home/core.nix

        ../../home/modules/hyprland
        ../../home/modules/gnome
        ../../home/modules/kitty.nix
        ../../home/modules/vscode
        ../../home/modules/common.nix
        ../../home/modules/git.nix
        ../../home/modules/bash.nix
        ../../home/modules/pkgs.nix
        ../../home/modules/neovim.nix
        ../../home/modules/tmux.nix
        ../../home/modules/fuzzel.nix
        ../../home/modules/playwright.nix
        ../../home/modules/vesktop.nix
        ../../home/modules/lazygit.nix
      ];
    };
  };
}
