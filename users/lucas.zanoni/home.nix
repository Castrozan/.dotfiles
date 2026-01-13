{
  imports = [
    ./pkgs.nix
    ./scripts

    ./home/git.nix
    ./home/ssh.nix
    ./home/asoundrc.nix
    ./home/session-vars.nix

    ../../home/core.nix
    ../../home/scripts
    ../../home/modules/bananas.nix
    ../../home/modules/cbonsai.nix
    ../../home/modules/claude
    # ../../home/modules/clipse.nix # TODO: clipse service is broken
    ../../home/modules/cmatrix.nix
    ../../home/modules/cursor
    ../../home/modules/flameshot.nix
    # ../../home/modules/greatshot.nix # Im using gnome native capture with ksnip for annotation for now
    ../../home/modules/fish.nix
    ../../home/modules/gnome/dconf.nix
    ../../home/modules/gnome/extension-manager.nix
    ../../home/modules/k9s.nix
    ../../home/modules/ksnip.nix
    ../../home/modules/install-nothing.nix
    ../../home/modules/kitty.nix
    ../../home/modules/lazygit.nix
    ../../home/modules/neovim.nix
    ../../home/modules/opencode.nix
    ../../home/modules/readItNow.nix
    ../../home/modules/sdkman.nix
    ../../home/modules/suwayomi-server.nix
    ../../home/modules/tmux.nix
    ../../home/modules/tuisvn.nix
    ../../home/modules/tui-notifier.nix
    ../../home/modules/vial.nix
    ../../home/modules/vscode
    ../../home/modules/wezterm.nix # https://tmuxai.dev/terminal-compatibility/
    ../../home/modules/zed-editor.nix
  ];
}
