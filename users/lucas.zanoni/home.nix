{
  imports = [
    ../../home/core.nix

    ./pkgs.nix
    ./scripts

    ./home/git.nix
    ./home/ssh.nix

    ../../home/modules/clipse.nix
    ../../home/modules/cursor.nix
    ../../home/modules/flameshot.nix
    ../../home/modules/fish.nix
    ../../home/modules/gnome/dconf.nix
    ../../home/modules/k9s.nix
    ../../home/modules/kitty.nix
    ../../home/modules/lazygit.nix
    ../../home/modules/neovim.nix
    ../../home/modules/tmux.nix
    ../../home/modules/tui-notifier.nix
    ../../home/modules/readItNow.nix
    ../../home/modules/sdkman.nix
    ../../home/modules/vial.nix
    ../../home/modules/vscode
  ];
}
