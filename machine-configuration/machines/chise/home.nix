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
    ../../../machine-configuration/desktop/hyprland/hyprland-nixos.nix
    ../../../agent-harness/harnesses/opencode
    ../../../agent-harness/harnesses/pi
    ../../../home/base/testing

    ../../../machine-configuration/terminal/shell/bash/bash-home-manager.nix
    ../../../machine-configuration/terminal/emulators/kitty/kitty-home-manager.nix
    ../../../machine-configuration/terminal/multiplexer/tmux/tmux-home-manager.nix
    ../../../machine-configuration/terminal/workspace-manager/herdr/herdr-home-manager.nix
    ../../../machine-configuration/terminal/emulators/wezterm/wezterm-home-manager.nix
    ../../../machine-configuration/terminal/terminal-command-packages-home-manager.nix
    ../../../machine-configuration/terminal/visual-effects/cmatrix/cmatrix-home-manager.nix

    ../../../machine-configuration/editors/cursor/cursor-home-manager.nix
    ../../../machine-configuration/editors/neovim/neovim-home-manager.nix
    ../../../machine-configuration/editors/visual-studio-code/visual-studio-code-home-manager.nix
    ../../../machine-configuration/editors/editor-command-packages-home-manager.nix

    ../../../machine-configuration/browsers/firefox/firefox-home-manager.nix
    ../../../machine-configuration/browsers/chrome/chrome-global-linux-home-manager.nix

    ../../../machine-configuration/desktop/clipboard-history/clipse-home-manager.nix
    ../../../machine-configuration/desktop/fonts/fonts-home-manager.nix
    ../../../machine-configuration/desktop/screensaver/screensaver-home-manager.nix
    ../../../machine-configuration/desktop/application-launcher/fuzzel-home-manager.nix
    ../../../machine-configuration/desktop/screen-capture/screen-capture-command-packages-home-manager.nix

    ../../../machine-configuration/development/cost-monitoring/ccost-home-manager.nix
    ../../../machine-configuration/development/cost-monitoring/ccusage-home-manager.nix
    ../../../machine-configuration/development/development-environments/devenv-home-manager.nix
    ../../../machine-configuration/development/version-control/lazygit-home-manager.nix
    ../../../machine-configuration/development/model-context-protocol/mcporter-home-manager.nix
    ../../../machine-configuration/development/version-control/git-fzf-home-manager.nix

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
    ../../../machine-configuration/development/development-environments/ralph-tui-home-manager.nix
    ../../../machine-configuration/desktop/vial/vial-home-manager.nix
    ../../../home/base/media/obsidian
    ../../../home/base/media/summarize.nix
    ../../../home/base/media/viu.nix
  ]
  ++ lib.optionals chisePrivateConfigExists [
    "${privateConfigRoot}/machines/chise/clawde-agents"
  ];
}
