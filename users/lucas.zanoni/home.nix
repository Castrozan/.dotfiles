{
  imports = [
    ../../home/core.nix

    ./pkgs.nix
    ./scripts

    ./home/git.nix

    ../../home/modules/neovim.nix
    ../../home/modules/kitty.nix
    ../../home/modules/fish.nix
    ../../home/modules/tmux.nix
    ../../home/modules/lazygit.nix
    ../../home/modules/dooit.nix
    ../../home/modules/k9s.nix
    ../../home/modules/pipx.nix
    ../../home/modules/sdkman.nix
    ../../home/modules/gnome/dconf.nix
    ../../home/modules/flameshot.nix
    ../../home/modules/tui-notifier.nix
  ];
}
