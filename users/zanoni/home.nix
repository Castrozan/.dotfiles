# Zanoni's Home Manager Configuration
{
  imports = [
    ./home/git.nix
    ./home/ssh.nix
    ./home/session-vars.nix

    ../../home/core.nix
    ../../home/scripts
    ../../home/modules/bash.nix
    ../../home/modules/cbonsai.nix
    ../../home/modules/claude
    ../../home/modules/clipse.nix
    ../../home/modules/cmatrix.nix
    ../../home/modules/cursor
    ../../home/modules/fish.nix
    ../../home/modules/fonts.nix
    ../../home/modules/fuzzel.nix
    ../../home/modules/gnome
    ../../home/modules/hyprland
    ../../home/modules/ksnip.nix
    ../../home/modules/install-nothing.nix
    ../../home/modules/kitty.nix
    ../../home/modules/lazygit.nix
    ../../home/modules/mpv.nix
    ../../home/modules/neovim.nix
    ../../home/modules/obsidian.nix
    ../../home/modules/opencode.nix
    ../../home/modules/pkgs.nix
    ../../home/modules/suwayomi-server.nix
    ../../home/modules/tmux.nix
    ../../home/modules/vesktop.nix
    ../../home/modules/vial.nix
    ../../home/modules/vscode
    ../../home/modules/voxtype.nix
    ../../home/modules/wezterm.nix # https://tmuxai.dev/terminal-compatibility/
    ../../home/modules/whisper-input
  ];
}
