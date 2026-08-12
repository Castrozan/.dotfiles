{ inputs, ... }:
{
  imports = [
    ./user-packages-lucas-zanoni-home-manager.nix

    ../development/version-control/git-private-home-manager.nix
    ../network/ssh/ssh-private-home-manager.nix
    ./session-variables-lucas-zanoni-home-manager.nix
    ../../agent-harness/harnesses/clawde/agents/steward.nix

    ./shared-home-manager-core.nix

    ../../agent-harness/agent-instructions/agent-instructions-home-manager.nix

    ../../agent-harness/harnesses/claude-code
    ../../agent-harness/harnesses/clawde
    ../../agent-harness/harnesses/codex
    ../../agent-harness/harnesses/hermes
    ../../agent-harness/harnesses/opencode
    ../development/testing/testing-home-manager.nix

    ../terminal/shell/bash/bash-home-manager.nix
    ../terminal/emulators/kitty/kitty-home-manager.nix
    ../terminal/terminal-command-packages-home-manager.nix
    ../terminal/multiplexer/tmux/tmux-home-manager.nix
    ../terminal/workspace-manager/herdr/herdr-home-manager.nix
    ../terminal/emulators/wezterm/wezterm-home-manager.nix
    ../terminal/file-manager/yazi/yazi-home-manager.nix

    ../editors/neovim/neovim-home-manager.nix

    ../desktop/theming/theming-home-manager.nix
    ../desktop/hammerspoon/hammerspoon-home-manager.nix
    ../desktop/application-launcher/application-launcher-home-manager.nix
    ../desktop/screensaver/screensaver-home-manager.nix
    ../browsers/brave/brave-profile-preferences-home-manager.nix
    ../browsers/chrome/chrome-profile-launchers-home-manager.nix
    ../desktop/fonts/fonts-home-manager.nix
    ../desktop/karabiner/karabiner-home-manager.nix
    ../desktop/keyboard-layout/keyboard-layout-home-manager.nix
    ../desktop/clipboard-history/maccy-home-manager.nix
    ../home-automation/home-assistant/home-assistant-remote-home-manager.nix

    ../development/cost-monitoring/ccost-home-manager.nix
    ../development/cost-monitoring/ccusage-home-manager.nix
    ../development/development-environments/devenv-home-manager.nix
    ../development/version-control/git-home-manager.nix
    ../development/version-control/glab-home-manager.nix
    ../development/issue-tracking/jira-home-manager.nix
    ../development/version-control/lazygit-home-manager.nix
    ../development/version-control/git-fzf-home-manager.nix

    # ../../machine-configuration/terminal/visual-effects/bad-apple/bad-apple-home-manager.nix  # disabled on darwin: pulls latest.yt-dlp -> deno -> rusty-v8 (V8 build takes 30+ min on aarch64-darwin)
    ../terminal/visual-effects/cbonsai/cbonsai-home-manager.nix
    ../terminal/visual-effects/cmatrix/cmatrix-home-manager.nix

    ../security/secrets/agenix-home-manager.nix
    ../security/password-manager/bitwarden-home-manager.nix

    ../network/tailscale/tailscale-daemon-home-manager.nix

    ../terminal/workspace-manager/cockpit-session-bridge/cockpit-session-bridge-home-manager.nix
    ../network/cloudflare-tunnel-connector/cloudflare-tunnel-connector-home-manager.nix

    ../media/obsidian/obsidian-home-manager.nix
    ../media/zathura/zathura-home-manager.nix

    "${inputs.private-config}/sb-toolkit"
  ];
}
