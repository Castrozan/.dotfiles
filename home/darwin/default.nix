{ inputs, ... }:
{
  imports = [
    ../base/packages/lucas-zanoni.nix

    ../base/dev/git-private.nix
    ../base/network/ssh-private.nix
    ../base/system/session-vars-lucas-zanoni.nix
    ../base/claude/clawde-agents/steward.nix

    ../base/core.nix

    ../base/agents

    ../base/claude
    ../base/codex
    ../base/hermes
    ../base/testing

    ../base/terminal/bash.nix
    ../base/terminal/kitty.nix
    ../base/terminal/scripts.nix
    ../base/terminal/tmux.nix
    ../base/terminal/herdr.nix
    ../base/terminal/wezterm.nix
    ../base/terminal/yazi

    ../base/editor/neovim.nix

    ../base/desktop/theming
    ./desktop/hammerspoon
    ./desktop/application-launcher
    ../base/desktop/screensaver
    ./desktop/brave
    ./desktop/chrome
    ../base/desktop/fonts.nix
    ./desktop/karabiner
    ./desktop/keyboard-layout
    ./desktop/maccy.nix
    ../base/desktop/home-assistant-remote.nix

    ../base/dev/ccost.nix
    ../base/dev/ccusage.nix
    ../base/dev/devenv.nix
    ../base/dev/git.nix
    ../base/dev/glab.nix
    ../base/dev/jira.nix
    ../base/dev/lazygit.nix
    ../base/dev/scripts.nix

    # ../base/terminal/bad-apple.nix  # disabled on darwin: pulls latest.yt-dlp -> deno -> rusty-v8 (V8 build takes 30+ min on aarch64-darwin)
    ../base/terminal/cbonsai.nix
    ../base/terminal/cmatrix.nix

    ../base/security/agenix.nix

    ../base/network/tailscale-daemon.nix

    ./cockpit-session-bridge
    ./cloudflare-tunnel-connector

    ../base/media/obsidian
    ../base/media/zathura

    "${inputs.private-config}/sb-toolkit"
  ];
}
