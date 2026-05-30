{ inputs, ... }:
{
  imports = [
    ../../base/packages/lucas-zanoni.nix

    ../../base/dev/git-private.nix
    ../../base/dev/git-toggle-user.nix
    ../../base/network/ssh-private.nix
    ../../base/system/session-vars-lucas-zanoni.nix
    ../../base/claude/agents/silver.nix
    ../../base/claude/agents/jojo-clawde-agents.nix

    ../../base/core.nix

    ../../base/agents

    ../../base/claude
    ../../base/codex
    ../../base/opencode
    ../../base/opencode/private.nix
    ../../base/testing

    ../../base/terminal/atuin.nix
    ../../base/terminal/fish.nix
    ../../base/terminal/kitty.nix
    ../../base/terminal/scripts.nix
    ../../base/terminal/tmux.nix
    ../../base/terminal/wezterm.nix
    ../../base/terminal/yazi

    ../../base/editor/jetbrains-idea.nix
    ../../base/editor/neovim.nix
    ../../base/editor/scripts.nix
    ../../base/editor/zed-editor.nix

    ../../base/browser/firefox.nix

    ../../base/desktop/theming
    ../../darwin/desktop/aerospace.nix
    ../../darwin/desktop/application-launcher
    ../../darwin/desktop/brave
    ../../darwin/desktop/workspace-navigator
    ../../darwin/desktop/workspace-switcher-client
    ../../base/desktop/fonts.nix
    ../../darwin/desktop/karabiner
    ../../darwin/desktop/keyboard-layout
    ../../darwin/desktop/maccy.nix
    ../../darwin/desktop/spaceman.nix
    ../../darwin/desktop/summon-browser
    ../../darwin/desktop/home-assistant-remote.nix

    ../../base/dev/devenv.nix
    ../../base/dev/git.nix
    ../../base/dev/glab.nix
    ../../base/dev/google-workspace-cli.nix
    ../../base/dev/jira.nix
    ../../base/dev/lazygit.nix
    ../../base/dev/mcporter.nix
    ../../base/dev/ralph-tui.nix
    ../../base/dev/scripts.nix
    ../../base/dev/tuisvn.nix

    # ../../base/terminal/bad-apple.nix  # disabled on darwin: pulls latest.yt-dlp -> deno -> rusty-v8 (V8 build takes 30+ min on aarch64-darwin)
    ../../base/terminal/cbonsai.nix
    ../../base/terminal/cmatrix.nix

    ../../base/security/agenix.nix

    ../../base/network/tailscale-daemon.nix

    ../../base/media/obsidian
    ../../base/media/zathura

    "${inputs.private-config}/sb-toolkit"
  ];
}
