# Zanoni's Home Manager Configuration — Clever 🤖
{
  imports = [
    ./home/git.nix
    ./home/ssh.nix
    ./home/session-vars.nix
    ./home/openclaw.nix

    ../../home/core.nix
    ../../home/scripts
    ../../home/modules/atuin.nix
    ../../home/modules/bad-apple.nix
    ../../home/modules/bluetui.nix
    ../../home/modules/bruno.nix
    ../../home/modules/cbonsai.nix
    ../../home/modules/ccost.nix
    ../../home/modules/clipse.nix
    ../../home/modules/openclaw
    ../../home/modules/qmd.nix

    ../../home/modules/claude
    ../../home/modules/codex
    ../../home/modules/cmatrix.nix
    ../../home/modules/cursor
    ../../home/modules/devenv.nix
    ../../home/modules/fish.nix
    ../../home/modules/fonts.nix
    ../../home/modules/fuzzel.nix
    ../../home/modules/gnome
    ../../home/modules/hyprland/nixos.nix
    ../../home/modules/install-nothing.nix
    ../../home/modules/kitty.nix
    ../../home/modules/lazygit.nix
    ../../home/modules/ani-cli.nix
    ../../home/modules/neovim.nix
    ../../home/modules/obsidian.nix
    ../../home/modules/opencode
    # ../../home/modules/ollama  # TEMP: disabled — corrupted download in nix store, re-enable after nix-collect-garbage
    ../../home/modules/pkgs.nix
    ../../home/modules/ralph-tui.nix
    ../../home/modules/suwayomi-server.nix
    ../../home/modules/tmux.nix
    ../../home/modules/vesktop.nix
    ../../home/modules/vial.nix
    ../../home/modules/vscode
    ../../home/modules/voxtype.nix
    ../../home/modules/wezterm.nix # https://tmuxai.dev/terminal-compatibility/
    ../../home/modules/whisp-away.nix
    ../../home/modules/systemd-manager-tui.nix
    ../../home/modules/testing
  ];
}
