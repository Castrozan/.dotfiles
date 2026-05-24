{
  imports = [
    ../pkgs.nix
    ../scripts

    ../home/git.nix
    ../home/hyprland.nix
    ../home/ssh.nix
    ../home/session-vars.nix
    ../home/clawde-agents.nix
    ../home/sophos-disable-plugins
    ../home/forticlient-disable-update

    ../../../home/base/core.nix

    ../../../home/base/agents
    ../../../home/base/security
    ../../../home/linux/audio
    ../../../home/base/claude
    ../../../home/base/codex
    ../../../home/linux/gnome/dconf.nix
    ../../../home/linux/gnome/extension-manager.nix
    ../../../home/linux/hyprland/standalone.nix
    ../../../home/base/opencode
    ../../../home/base/opencode/private.nix
    ../../../home/base/sourcebot
    ../../../home/base/testing

    ../../../home/base/terminal/atuin.nix
    ../../../home/base/terminal/fish.nix
    ../../../home/base/terminal/kitty.nix
    ../../../home/base/terminal/tmux.nix
    ../../../home/base/terminal/wezterm.nix
    ../../../home/base/terminal/yazi
    ../../../home/base/terminal/scripts.nix

    ../../../home/base/editor/cursor
    ../../../home/base/editor/jetbrains-idea.nix
    ../../../home/base/editor/neovim.nix
    ../../../home/base/editor/vscode
    ../../../home/base/editor/zed-editor.nix
    ../../../home/base/editor/scripts.nix

    ../../../home/base/browser/chrome-global.nix
    ../../../home/base/browser/firefox.nix

    ../../../home/linux/desktop/bananas.nix
    ../../../home/linux/desktop/clipse.nix
    ../../../home/linux/desktop/flameshot.nix
    ../../../home/base/desktop/fonts.nix
    ../../../home/linux/desktop/ksnip.nix
    ../../../home/linux/desktop/scripts.nix

    ../../../home/base/dev/ccost.nix
    ../../../home/base/dev/devenv.nix
    ../../../home/base/dev/github-actions-runner.nix
    ../../../home/base/dev/glab.nix
    ../../../home/base/dev/google-workspace-cli.nix
    ../../../home/base/dev/lazygit.nix
    ../../../home/base/dev/mcporter.nix
    ../../../home/base/dev/scripts.nix

    ../../../home/base/media/ani-cli.nix
    ../../../home/base/media/bad-apple.nix
    ../../../home/base/media/obs-studio.nix
    ../../../home/base/media/suwayomi-server.nix
    ../../../home/base/media/zathura
    ../../../home/base/media/scripts.nix

    ../../../home/linux/network/forticlient
    ../../../home/linux/network/network-optimization.nix
    ../../../home/linux/network/openfortivpn
    ../../../home/base/network/tailscale-daemon.nix

    ../../../home/linux/system/lid-switch-ignore.nix
    ../../../home/linux/system/oom-protection.nix
    ../../../home/base/system/stale-symlink-cleanup.nix
    ../../../home/base/system/scripts.nix
    ../../../home/linux/system/ubuntu-system-tuning.nix

    ../../../home/linux/voice/voice-pipeline.nix
    ../../../home/linux/voice/whisp-away.nix
    ../home/voice-pipeline.nix

    ../../../home/linux/home-assistant

    ../../../home/base/gaming/cbonsai.nix
    ../../../home/base/gaming/cmatrix.nix
    ../../../home/base/gaming/install-nothing.nix
    ../../../home/linux/gaming/vesktop.nix

    ../../../home/base/system/bluetui.nix
    ../../../home/base/system/systemd-manager-tui.nix
    ../../../home/base/dev/crabwalk.nix
    ../../../home/base/dev/k9s.nix
    ../../../home/base/dev/mongodb-compass.nix
    ../../../home/base/dev/ralph-tui.nix
    ../../../home/base/dev/tuisvn.nix
    ../../../home/base/gaming/gogcli.nix
    ../../../home/linux/desktop/tui-notifier.nix
    ../../../home/linux/desktop/vial.nix
    ../../../home/base/media/obsidian
    ../../../home/base/media/readItNow.nix
    ../../../home/base/media/summarize.nix
    ../../../home/base/media/viu.nix
  ];
}
