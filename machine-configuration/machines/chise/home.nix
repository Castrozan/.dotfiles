{ lib, ... }:
let
  privateConfigRoot = ../../../private-configuration;
  chisePrivateConfigExists = builtins.pathExists privateConfigRoot;
in
{
  imports = [
    ./home/git.nix
    ./home/hyprland.nix
    ./home/session-vars.nix
    ./home/chrome-default-browser.nix
    ../../../agent-harness/harnesses/clawde/agents/steward.nix
    ../../../agent-harness/harnesses/clawde/agents/ril-watcher

    ../shared-home-manager-core.nix

    ../../../agent-harness/agent-instructions/agent-instructions-home-manager.nix
    ../../security/security-home-manager.nix
    ../../audio/audio-home-manager.nix
    ../../../agent-harness/harnesses/claude-code
    ../../../agent-harness/harnesses/clawde
    ../../../agent-harness/harnesses/codex
    ../../desktop/gnome/gnome-home-manager.nix
    ../../home-automation/home-assistant/home-assistant-home-manager.nix
    ../../desktop/hyprland/hyprland-nixos.nix
    ../../../agent-harness/harnesses/opencode
    ../../development/testing/testing-home-manager.nix

    ../../terminal/shell/bash/bash-home-manager.nix
    ../../terminal/emulators/kitty/kitty-home-manager.nix
    ../../terminal/multiplexer/tmux/tmux-home-manager.nix
    ../../terminal/workspace-manager/herdr/herdr-home-manager.nix
    ../../terminal/emulators/wezterm/wezterm-home-manager.nix
    ../../terminal/terminal-command-packages-home-manager.nix
    ../../terminal/visual-effects/cmatrix/cmatrix-home-manager.nix

    ../../editors/cursor/cursor-home-manager.nix
    ../../editors/neovim/neovim-home-manager.nix
    ../../editors/visual-studio-code/visual-studio-code-home-manager.nix
    ../../editors/editor-command-packages-home-manager.nix

    ../../browsers/firefox/firefox-home-manager.nix
    ../../browsers/chrome/chrome-global-linux-home-manager.nix

    ../../desktop/clipboard-history/clipse-home-manager.nix
    ../../desktop/fonts/fonts-home-manager.nix
    ../../desktop/screensaver/screensaver-home-manager.nix
    ../../desktop/application-launcher/fuzzel-home-manager.nix
    ../../desktop/screen-capture/screen-capture-command-packages-home-manager.nix

    ../../development/cost-monitoring/ccost-home-manager.nix
    ../../development/cost-monitoring/ccusage-home-manager.nix
    ../../development/development-environments/devenv-home-manager.nix
    ../../development/version-control/lazygit-home-manager.nix
    ../../development/model-context-protocol/mcporter-home-manager.nix
    ../../development/version-control/git-fzf-home-manager.nix

    ../../media/anime-streaming/ani-cli-home-manager.nix
    ../../media/anime-streaming/seanime-home-manager.nix
    ../../terminal/visual-effects/bad-apple/bad-apple-chise-home-manager.nix
    ../../media/manga-streaming/suwayomi-server-home-manager.nix
    ../../media/media-command-packages-home-manager.nix
    ../../media/arr-stack/stack/arr-stack-home-manager.nix

    ../../operating-system/system-command-packages-home-manager.nix
    ../../operating-system/nix-store-maintenance/stale-symlink-cleanup-home-manager.nix

    ../../network/ssh/ssh-private-home-manager.nix

    ../../voice/hey-bot-home-manager.nix
    ../../voice/hey-bot-test-home-manager.nix
    ./home/hey-bot.nix
    ../../voice/voxtype-home-manager.nix
    ../../voice/whisp-away-home-manager.nix

    ../../terminal/visual-effects/cbonsai/cbonsai-chise-home-manager.nix
    ../../gaming/install-nothing/install-nothing-home-manager.nix
    ../../gaming/vesktop/vesktop-home-manager.nix

    ../../operating-system/bluetooth/bluetui-home-manager.nix
    ../../operating-system/service-management/systemd-manager-tui-home-manager.nix
    ../../development/development-environments/ralph-tui-home-manager.nix
    ../../desktop/vial/vial-home-manager.nix
    ../../media/obsidian/obsidian-home-manager.nix
    ../../media/content-summarization/summarize-home-manager.nix
    ../../media/terminal-media-viewer/viu-home-manager.nix
  ]
  ++ lib.optionals chisePrivateConfigExists [
    "${privateConfigRoot}/machines/chise/clawde-agents"
  ];
}
