{ inputs, ... }:
{
  imports = [
    ../base/packages/lucas-zanoni.nix

    ../base/dev/git-private.nix
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

    ../base/desktop/theming
    ./desktop/hammerspoon
    ./desktop/application-launcher
    ../base/desktop/screensaver
    ./desktop/brave
    ./desktop/chrome
    ../base/desktop/fonts.nix
    ./desktop/karabiner
    ./desktop/keyboard-layout
    ./desktop/maccy
    ../base/desktop/home-assistant-remote.nix

    ../base/dev/ccost.nix
    ../base/dev/ccusage.nix
    ../base/dev/devenv.nix
    ../base/dev/git.nix
    ../base/dev/glab.nix
    ../base/dev/jira.nix
    ../base/dev/lazygit.nix
    ../base/dev/scripts.nix

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
