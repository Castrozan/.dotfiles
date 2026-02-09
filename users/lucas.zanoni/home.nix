# Lucas.Zanoni's Home Manager Configuration — Romário ⚽
{
  xdg.configFile."hypr-host/monitors.conf".text = ''
    monitor = HDMI-A-1, 1920x1080@120, auto, 1
    monitor = eDP-1, disable
  '';

  imports = [
    ./pkgs.nix
    ./scripts

    ./home/git.nix
    ./home/ssh.nix
    ./home/session-vars.nix
    ./home/openclaw.nix

    ../../home/core.nix
    ../../home/scripts
    ../../home/modules/atuin.nix
    ../../home/modules/bad-apple.nix
    ../../home/modules/bananas.nix
    ../../home/modules/bluetui.nix
    ../../home/modules/cbonsai.nix
    ../../home/modules/ccost.nix
    ../../home/modules/codex
    ../../home/modules/openclaw
    ../../home/modules/qmd.nix
    ../../home/modules/claude
    #../../home/modules/clipse.nix TODO: clipse service does no work with gnome, migrate docs/clipse-gnome-issues.md
    ../../home/modules/cmatrix.nix
    ../../home/modules/cursor
    ../../home/modules/devenv.nix
    ../../home/modules/flameshot.nix
    ../../home/modules/fish.nix
    ../../home/modules/fonts.nix
    ../../home/modules/glab.nix
    ../../home/modules/gnome/dconf.nix
    ../../home/modules/gnome/extension-manager.nix
    ../../home/modules/hyprland/standalone.nix
    ../../home/modules/install-nothing.nix
    ../../home/modules/k9s.nix
    ../../home/modules/kitty.nix
    ../../home/modules/lazygit.nix
    ../../home/modules/mongodb-compass.nix
    ../../home/modules/neovim.nix
    ../../home/modules/obsidian.nix
    ../../home/modules/opencode
    ../../home/modules/opencode/private.nix
    ../../home/modules/openfortivpn
    ../../home/modules/ralph-tui.nix
    ../../home/modules/readItNow.nix
    ../../home/modules/sourcebot
    ../../home/modules/suwayomi-server.nix
    ../../home/modules/tailscale-daemon.nix
    ../../home/modules/tmux.nix
    ../../home/modules/tuisvn.nix
    ../../home/modules/tui-notifier.nix
    ../../home/modules/systemd-manager-tui.nix
    ../../home/modules/vial.nix
    ../../home/modules/vscode
    ../../home/modules/vesktop.nix
    ../../home/modules/yazi.nix
    ../../home/modules/wezterm.nix # https://tmuxai.dev/terminal-compatibility/
    ../../home/modules/whisp-away.nix
    # ../../home/modules/hey-bot.nix
    # ./home/hey-bot.nix
    ../../home/modules/zed-editor.nix
    ../../home/modules/testing
    ../../home/modules/ani-cli.nix
    ../../home/modules/audio
  ];
}
