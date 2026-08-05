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
    ../../../machine-configuration/audio/audio-home-manager.nix
    ../../../agent-harness/harnesses/claude-code
    ../../../agent-harness/harnesses/clawde
    ../../../agent-harness/harnesses/codex
    ../../../machine-configuration/desktop/gnome/gnome-home-manager.nix
    ../../../machine-configuration/home-automation/home-assistant/home-assistant-home-manager.nix
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

    ../../../machine-configuration/media/anime-streaming/ani-cli-home-manager.nix
    ../../../machine-configuration/terminal/visual-effects/bad-apple/bad-apple-chise-home-manager.nix
    ../../../machine-configuration/media/manga-streaming/suwayomi-server-home-manager.nix
    ../../../machine-configuration/media/media-command-packages-home-manager.nix
    ../../../machine-configuration/media/arr-stack/stack/arr-stack-home-manager.nix

    ../../../home/base/system/scripts.nix
    ../../../home/base/system/stale-symlink-cleanup.nix

    ../../../machine-configuration/voice/hey-bot-home-manager.nix
    ../../../machine-configuration/voice/hey-bot-test-home-manager.nix
    ./home/hey-bot.nix
    ../../../machine-configuration/voice/voxtype-home-manager.nix
    ../../../machine-configuration/voice/whisp-away-home-manager.nix

    ../../../machine-configuration/terminal/visual-effects/cbonsai/cbonsai-chise-home-manager.nix
    ../../../machine-configuration/gaming/install-nothing/install-nothing-home-manager.nix
    ../../../machine-configuration/gaming/vesktop/vesktop-home-manager.nix

    ../../../home/base/system/bluetui.nix
    ../../../home/base/system/systemd-manager-tui.nix
    ../../../machine-configuration/development/development-environments/ralph-tui-home-manager.nix
    ../../../machine-configuration/desktop/vial/vial-home-manager.nix
    ../../../machine-configuration/media/obsidian/obsidian-home-manager.nix
    ../../../machine-configuration/media/content-summarization/summarize-home-manager.nix
    ../../../machine-configuration/media/terminal-media-viewer/viu-home-manager.nix
  ]
  ++ lib.optionals chisePrivateConfigExists [
    "${privateConfigRoot}/machines/chise/clawde-agents"
  ];
}
