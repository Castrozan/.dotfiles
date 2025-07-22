{
  imports = [
    ../../home/core.nix
    ./pkgs.nix

    ./home/git.nix

    ../../home/modules/neovim.nix
    ../../home/modules/kitty.nix
    ../../home/modules/tmux.nix
    ../../home/modules/lazygit.nix
    ../../home/modules/dooit.nix
    ../../home/modules/pipx.nix
    ../../home/modules/sdkman.nix
    ../../home/modules/gnome/dconf.nix
  ];
}
