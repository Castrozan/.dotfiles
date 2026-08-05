{ lib, ... }:
let
  privateConfigRoot = ../../../private-config;
  chisePrivateConfigExists = builtins.pathExists privateConfigRoot;
in
{
  imports = [
    ./home/git.nix
    ./home/hyprland.nix
    ./home/ssh.nix
    ./home/session-vars.nix
    ./home/chrome-default-browser.nix
    ../../../agent-harness/harnesses/clawde/agents/steward.nix
    ../../../agent-harness/harnesses/clawde/agents/ril-watcher

    ../../../home/base/core.nix

    ../../../agent-harness/agent-instructions/agent-instructions-home-manager.nix
    ../../../home/base/security
    ../../../home/linux/audio
    ../../../agent-harness/harnesses/claude-code
    ../../../agent-harness/harnesses/clawde
    ../../../agent-harness/harnesses/codex
    ../../../home/linux/gnome
    ../../../home/linux/home-assistant
    ../../../home/linux/hyprland/nixos.nix
    ../../../agent-harness/harnesses/opencode
    ../../../agent-harness/harnesses/pi
    ../../../home/base/testing

    ../../../home/base/terminal/bash.nix
    ../../../home/base/terminal/kitty.nix
    ../../../home/base/terminal/tmux.nix
    ../../../home/base/terminal/herdr.nix
    ../../../home/base/terminal/wezterm.nix
    ../../../home/base/terminal/scripts.nix
    ../../../home/base/terminal/cmatrix.nix

    ../../../home/base/editor/cursor
    ../../../home/base/editor/neovim.nix
    ../../../home/base/editor/vscode
    ../../../home/base/editor/scripts.nix

    ../../../home/base/browser/firefox.nix
    ../../../home/base/browser/chrome-global.nix

    ../../../home/linux/desktop/clipse.nix
    ../../../home/base/desktop/fonts.nix
    ../../../home/base/desktop/screensaver
    ../../../home/linux/desktop/fuzzel.nix
    ../../../home/linux/desktop/scripts.nix

    ../../../home/base/dev/ccost.nix
    ../../../home/base/dev/ccusage.nix
    ../../../home/base/dev/devenv.nix
    ../../../home/base/dev/lazygit.nix
    ../../../home/base/dev/mcporter.nix
    ../../../home/base/dev/scripts.nix

    ../../../home/base/media/ani-cli.nix
    ../../../home/base/media/bad-apple.nix
    ../../../home/base/media/suwayomi-server.nix
    ../../../home/base/media/scripts.nix
    ../../../home/linux/arr-stack

    ../../../home/base/system/scripts.nix
    ../../../home/base/system/stale-symlink-cleanup.nix

    ../../../home/linux/voice/hey-bot.nix
    ../../../home/linux/voice/hey-bot-test.nix
    ./home/hey-bot.nix
    ../../../home/linux/voice/voxtype.nix
    ../../../home/linux/voice/whisp-away.nix

    ../../../home/base/gaming/cbonsai.nix
    ../../../home/base/gaming/install-nothing.nix
    ../../../home/linux/gaming/vesktop.nix

    ../../../home/base/system/bluetui.nix
    ../../../home/base/system/systemd-manager-tui.nix
    ../../../home/base/dev/ralph-tui.nix
    ../../../home/linux/desktop/vial.nix
    ../../../home/base/media/obsidian
    ../../../home/base/media/summarize.nix
    ../../../home/base/media/viu.nix
  ]
  ++ lib.optionals chisePrivateConfigExists [
    "${privateConfigRoot}/machines/chise/clawde-agents"
  ];
}
