{
  imports = [
    ./pkgs.nix
    ./scripts

    ./home/git.nix
    ./home/hyprland.nix
    ./home/ssh.nix
    ./home/session-vars.nix
    ./home/openclaw.nix

    ../../home/core.nix

    ../../home/modules/agents
    ../../home/modules/security
    ../../home/modules/audio
    ../../home/modules/claude
    ../../home/modules/codex
    ../../home/modules/gnome/dconf.nix
    ../../home/modules/gnome/extension-manager.nix
    ../../home/modules/hyprland/standalone.nix
    ../../home/modules/openclaw
    ../../home/modules/openclaw-mesh
    ../../home/modules/opencode
    ../../home/modules/opencode/private.nix
    ../../home/modules/sourcebot
    ../../home/modules/testing

    ../../home/modules/terminal/atuin.nix
    ../../home/modules/terminal/fish.nix
    ../../home/modules/terminal/kitty.nix
    ../../home/modules/terminal/tmux.nix
    ../../home/modules/terminal/wezterm.nix
    ../../home/modules/terminal/yazi.nix
    ../../home/modules/terminal/scripts.nix

    ../../home/modules/editor/cursor
    ../../home/modules/editor/jetbrains-idea.nix
    ../../home/modules/editor/neovim.nix
    ../../home/modules/editor/vscode
    ../../home/modules/editor/zed-editor.nix
    ../../home/modules/editor/scripts.nix

    ../../home/modules/browser/chrome-global.nix
    ../../home/modules/browser/firefox.nix

    ../../home/modules/desktop/bananas.nix
    ../../home/modules/desktop/clipse.nix
    ../../home/modules/desktop/flameshot.nix
    ../../home/modules/desktop/fonts.nix
    ../../home/modules/desktop/ksnip.nix
    ../../home/modules/desktop/scripts.nix

    ../../home/modules/dev/ccost.nix
    ../../home/modules/dev/devenv.nix
    ../../home/modules/dev/glab.nix
    ../../home/modules/dev/google-workspace-cli.nix
    ../../home/modules/dev/lazygit.nix
    ../../home/modules/dev/mcporter.nix
    ../../home/modules/dev/scripts.nix

    ../../home/modules/media/ani-cli.nix
    ../../home/modules/media/bad-apple.nix
    ../../home/modules/media/obs-studio.nix
    ../../home/modules/media/suwayomi-server.nix
    ../../home/modules/media/youtube.nix
    ../../home/modules/media/scripts.nix

    ../../home/modules/network/network-optimization.nix
    ../../home/modules/network/openfortivpn
    ../../home/modules/network/tailscale-daemon.nix

    ../../home/modules/system/lid-switch-ignore.nix
    ../../home/modules/system/oom-protection.nix
    ../../home/modules/system/stale-symlink-cleanup.nix
    ../../home/modules/system/scripts.nix
    ../../home/modules/system/ubuntu-system-tuning.nix

    ../../home/modules/voice/hey-bot.nix
    ./home/hey-bot.nix
    ../../home/modules/voice/voice-pipeline.nix
    ./home/voice-pipeline.nix
    ../../home/modules/voice/whisp-away.nix

    ../../home/modules/home-assistant

    ../../home/modules/gaming/cbonsai.nix
    ../../home/modules/gaming/cmatrix.nix
    ../../home/modules/gaming/install-nothing.nix
    ../../home/modules/gaming/vesktop.nix

    ../../home/modules/system/bluetui.nix
    ../../home/modules/system/systemd-manager-tui.nix
    ../../home/modules/dev/crabwalk.nix
    ../../home/modules/dev/k9s.nix
    ../../home/modules/dev/mongodb-compass.nix
    ../../home/modules/dev/ralph-tui.nix
    ../../home/modules/dev/tuisvn.nix
    ../../home/modules/gaming/gogcli.nix
    ../../home/modules/desktop/tui-notifier.nix
    ../../home/modules/desktop/vial.nix
    ../../home/modules/media/obsidian.nix
    ../../home/modules/media/obsidian-headless-sync.nix
    ../../home/modules/media/readItNow.nix
    ../../home/modules/media/summarize.nix
    ../../home/modules/media/twitter.nix
    ../../home/modules/media/viu.nix
  ];
}
