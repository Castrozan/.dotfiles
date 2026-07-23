{ lib, ... }:
let
  privateConfigRoot = ../../../private-config;
  chisePrivateConfigExists = builtins.pathExists privateConfigRoot;
in
{
  imports = [
    ./chise/git.nix
    ./chise/hyprland.nix
    ./chise/ssh.nix
    ./chise/session-vars.nix
    ./chise/chrome-default-browser.nix
    ../../base/claude/clawde-agents/steward.nix

    ../../base/core.nix

    ../../base/agents
    ../../base/security
    ../../linux/audio
    ../../base/claude
    ../../base/codex
    ../../linux/gnome
    ../../linux/home-assistant
    ../../linux/hyprland/nixos.nix
    ../../base/opencode
    ../../base/testing

    ../../base/terminal/bash.nix
    ../../base/terminal/kitty.nix
    ../../base/terminal/tmux.nix
    ../../base/terminal/herdr.nix
    ../../base/terminal/wezterm.nix
    ../../base/terminal/scripts.nix
    ../../base/terminal/cmatrix.nix

    ../../base/editor/cursor
    ../../base/editor/neovim.nix
    ../../base/editor/vscode
    ../../base/editor/scripts.nix

    ../../base/browser/firefox.nix
    ../../base/browser/chrome-global.nix

    ../../linux/desktop/clipse.nix
    ../../base/desktop/fonts.nix
    ../../base/desktop/screensaver
    ../../linux/desktop/fuzzel.nix
    ../../linux/desktop/scripts.nix

    ../../base/dev/ccost.nix
    ../../base/dev/ccusage.nix
    ../../base/dev/devenv.nix
    ../../base/dev/lazygit.nix
    ../../base/dev/mcporter.nix
    ../../base/dev/scripts.nix

    ../../base/media/ani-cli.nix
    ../../base/media/bad-apple.nix
    ../../base/media/suwayomi-server.nix
    ../../base/media/scripts.nix
    ../../linux/arr-stack

    ../../base/system/scripts.nix
    ../../base/system/stale-symlink-cleanup.nix

    ../../linux/voice/hey-bot.nix
    ../../linux/voice/hey-bot-test.nix
    ./chise/hey-bot.nix
    ../../linux/voice/voxtype.nix
    ../../linux/voice/whisp-away.nix

    ../../base/gaming/cbonsai.nix
    ../../base/gaming/install-nothing.nix
    ../../linux/gaming/vesktop.nix

    ../../base/system/bluetui.nix
    ../../base/system/systemd-manager-tui.nix
    ../../base/dev/ralph-tui.nix
    ../../linux/desktop/vial.nix
    ../../base/media/obsidian
    ../../base/media/summarize.nix
    ../../base/media/viu.nix
  ]
  ++ lib.optionals chisePrivateConfigExists [
    "${privateConfigRoot}/machines/chise/clawde-agents"
  ];
}
