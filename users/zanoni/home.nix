{
  imports = [
    ./home/git.nix
    ./home/hyprland.nix
    ./home/ssh.nix
    ./home/session-vars.nix
    ./home/openclaw.nix

    ../../home/core.nix
    ../../home/scripts

    ../../home/modules/security
    ../../home/modules/audio
    ../../home/modules/claude
    ../../home/modules/codex
    ../../home/modules/gnome
    ../../home/modules/hyprland/nixos.nix
    ../../home/modules/openclaw
    ../../home/modules/openclaw-mesh
    ../../home/modules/opencode
    ../../home/modules/testing

    ../../home/modules/terminal/atuin.nix
    ../../home/modules/terminal/fish.nix
    ../../home/modules/terminal/kitty.nix
    ../../home/modules/terminal/tmux.nix
    ../../home/modules/terminal/wezterm.nix
    ../../home/modules/terminal/scripts.nix

    ../../home/modules/editor/cursor
    ../../home/modules/editor/neovim.nix
    ../../home/modules/editor/vscode

    ../../home/modules/browser/firefox.nix
    ../../home/modules/browser/scripts.nix

    ../../home/modules/desktop/clipse.nix
    ../../home/modules/desktop/fonts.nix
    ../../home/modules/desktop/fuzzel.nix
    ../../home/modules/desktop/scripts.nix

    ../../home/modules/dev/bruno.nix
    ../../home/modules/dev/ccost.nix
    ../../home/modules/dev/devenv.nix
    ../../home/modules/dev/lazygit.nix
    ../../home/modules/dev/mcporter.nix
    ../../home/modules/dev/scripts.nix

    ../../home/modules/media/ani-cli.nix
    ../../home/modules/media/bad-apple.nix
    ../../home/modules/media/suwayomi-server.nix
    ../../home/modules/media/scripts.nix

    ../../home/modules/system/scripts.nix

    ../../home/modules/voice/hey-bot.nix
    ../../home/modules/voice/hey-bot-test.nix
    ./home/hey-bot.nix
    ../../home/modules/voice/voice-pipeline.nix
    ./home/voice-pipeline.nix
    ../../home/modules/voice/voxtype.nix
    ../../home/modules/voice/whisp-away.nix

    ../../home/modules/gaming/cbonsai.nix
    ../../home/modules/gaming/cmatrix.nix
    ../../home/modules/gaming/install-nothing.nix
    ../../home/modules/gaming/vesktop.nix

    ../../home/modules/bluetui.nix
    ../../home/modules/obsidian.nix
    ../../home/modules/pkgs.nix
    ../../home/modules/ralph-tui.nix
    ../../home/modules/summarize.nix
    ../../home/modules/systemd-manager-tui.nix
    ../../home/modules/vial.nix
    ../../home/modules/viu.nix
  ];
}
