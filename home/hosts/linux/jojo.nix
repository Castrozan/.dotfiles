{
  imports = [
    ../../base/packages/lucas-zanoni.nix
    ../../base/dev/git-toggle-user.nix

    ../../base/dev/git-private.nix
    ../../linux/hyprland/jojo-monitors.nix
    ../../base/network/ssh-private.nix
    ../../base/system/session-vars-lucas-zanoni.nix
    ../../base/claude/agents/jojo-clawde-agents.nix
    ../../base/claude/agents/steward.nix
    ../../linux/system/sophos-disable-plugins
    ../../linux/system/forticlient-disable-update

    ../../base/core.nix

    ../../base/agents
    ../../base/security
    ../../linux/audio
    ../../base/claude
    ../../base/codex
    ../../linux/gnome/dconf.nix
    ../../linux/gnome/extension-manager.nix
    ../../linux/hyprland/standalone.nix
    ../../base/opencode
    ../../base/opencode/private.nix
    ../../base/sourcebot
    ../../base/testing

    ../../base/terminal/atuin.nix
    ../../base/terminal/fish.nix
    ../../base/terminal/kitty.nix
    ../../base/terminal/tmux.nix
    ../../base/terminal/wezterm.nix
    ../../base/terminal/yazi
    ../../base/terminal/scripts.nix

    ../../base/editor/cursor
    ../../base/editor/jetbrains-idea.nix
    ../../base/editor/neovim.nix
    ../../base/editor/vscode
    ../../base/editor/zed-editor.nix
    ../../base/editor/scripts.nix

    ../../base/browser/chrome-global.nix
    ../../base/browser/firefox.nix

    ../../linux/desktop/bananas.nix
    ../../linux/desktop/clipse.nix
    ../../linux/desktop/flameshot.nix
    ../../base/desktop/fonts.nix
    ../../linux/desktop/ksnip.nix
    ../../linux/desktop/scripts.nix

    ../../base/dev/aws.nix
    ../../base/dev/ccost.nix
    ../../base/dev/devenv.nix
    ../../base/dev/github-actions-runner.nix
    ../../base/dev/glab.nix
    ../../base/dev/google-workspace-cli.nix
    ../../base/dev/lazygit.nix
    ../../base/dev/mcporter.nix
    ../../base/dev/scripts.nix

    ../../base/media/ani-cli.nix
    ../../base/media/bad-apple.nix
    ../../base/media/obs-studio.nix
    ../../base/media/suwayomi-server.nix
    ../../base/media/zathura
    ../../base/media/scripts.nix

    ../../linux/network/forticlient
    ../../linux/network/network-optimization.nix
    ../../linux/network/openfortivpn
    ../../base/network/tailscale-daemon.nix

    ../../linux/system/lid-switch-ignore.nix
    ../../linux/system/oom-protection.nix
    ../../base/system/stale-symlink-cleanup.nix
    ../../base/system/scripts.nix
    ../../linux/system/ubuntu-system-tuning.nix

    ../../linux/voice/voice-pipeline.nix
    ../../linux/voice/whisp-away.nix
    ../../linux/voice/voice-pipeline-overrides.nix

    ../../linux/home-assistant

    ../../base/gaming/cbonsai.nix
    ../../base/gaming/cmatrix.nix
    ../../base/gaming/install-nothing.nix
    ../../linux/gaming/vesktop.nix

    ../../base/system/bluetui.nix
    ../../base/system/systemd-manager-tui.nix
    ../../base/dev/crabwalk.nix
    ../../base/dev/k9s.nix
    ../../base/dev/mongodb-compass.nix
    ../../base/dev/ralph-tui.nix
    ../../base/dev/tuisvn.nix
    ../../base/gaming/gogcli.nix
    ../../linux/desktop/tui-notifier.nix
    ../../linux/desktop/vial.nix
    ../../base/media/obsidian
    ../../base/media/readItNow.nix
    ../../base/media/summarize.nix
    ../../base/media/viu.nix
  ];
}
