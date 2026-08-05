{ inputs, ... }:
{
  imports = [
    ../base/packages/lucas-zanoni.nix

    ../../machine-configuration/development/version-control/git-private-home-manager.nix
    ../base/network/ssh-private.nix
    ../base/system/session-vars-lucas-zanoni.nix
    ../../agent-harness/harnesses/clawde/agents/steward.nix

    ../base/core.nix

    ../../agent-harness/agent-instructions/agent-instructions-home-manager.nix

    ../../agent-harness/harnesses/claude-code
    ../../agent-harness/harnesses/clawde
    ../../agent-harness/harnesses/codex
    ../../agent-harness/harnesses/hermes
    ../../agent-harness/harnesses/opencode
    ../../agent-harness/harnesses/opencode/private.nix
    ../../agent-harness/harnesses/pi
    ../base/testing

    ../../machine-configuration/terminal/shell/bash/bash-home-manager.nix
    ../../machine-configuration/terminal/emulators/kitty/kitty-home-manager.nix
    ../../machine-configuration/terminal/terminal-command-packages-home-manager.nix
    ../../machine-configuration/terminal/multiplexer/tmux/tmux-home-manager.nix
    ../../machine-configuration/terminal/workspace-manager/herdr/herdr-home-manager.nix
    ../../machine-configuration/terminal/emulators/wezterm/wezterm-home-manager.nix
    ../../machine-configuration/terminal/file-manager/yazi/yazi-home-manager.nix

    ../../machine-configuration/editors/neovim/neovim-home-manager.nix

    ../../machine-configuration/desktop/theming/theming-home-manager.nix
    ../../machine-configuration/desktop/hammerspoon/hammerspoon-home-manager.nix
    ../../machine-configuration/desktop/application-launcher/application-launcher-home-manager.nix
    ../../machine-configuration/desktop/screensaver/screensaver-home-manager.nix
    ../../machine-configuration/browsers/brave/brave-profile-preferences-home-manager.nix
    ../../machine-configuration/browsers/chrome/chrome-profile-launchers-home-manager.nix
    ../../machine-configuration/desktop/fonts/fonts-home-manager.nix
    ../../machine-configuration/desktop/karabiner/karabiner-home-manager.nix
    ./desktop/keyboard-layout
    ./desktop/maccy
    ../base/desktop/home-assistant-remote.nix

    ../../machine-configuration/development/cost-monitoring/ccost-home-manager.nix
    ../../machine-configuration/development/cost-monitoring/ccusage-home-manager.nix
    ../../machine-configuration/development/development-environments/devenv-home-manager.nix
    ../../machine-configuration/development/version-control/git-home-manager.nix
    ../../machine-configuration/development/version-control/glab-home-manager.nix
    ../../machine-configuration/development/issue-tracking/jira-home-manager.nix
    ../../machine-configuration/development/version-control/lazygit-home-manager.nix
    ../../machine-configuration/development/version-control/git-fzf-home-manager.nix

    # ../../machine-configuration/terminal/visual-effects/bad-apple/bad-apple-home-manager.nix  # disabled on darwin: pulls latest.yt-dlp -> deno -> rusty-v8 (V8 build takes 30+ min on aarch64-darwin)
    ../../machine-configuration/terminal/visual-effects/cbonsai/cbonsai-home-manager.nix
    ../../machine-configuration/terminal/visual-effects/cmatrix/cmatrix-home-manager.nix

    ../base/security/agenix.nix
    ../base/security/bitwarden.nix

    ../base/network/tailscale-daemon.nix

    ./cockpit-session-bridge
    ./cloudflare-tunnel-connector

    ../base/media/obsidian
    ../base/media/zathura

    "${inputs.private-config}/sb-toolkit"
  ];
}
