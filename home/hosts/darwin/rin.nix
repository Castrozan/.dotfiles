{ lib, inputs, ... }:
let
  privateConfigRoot = ../../../private-config;
  rinPrivateConfigExists = builtins.pathExists privateConfigRoot;
in
{
  imports = [
    ../../base/packages/lucas-zanoni.nix

    ../../base/dev/git-private.nix
    ../../base/network/ssh-private.nix
    ../../base/system/session-vars-lucas-zanoni.nix
    ../../base/claude/agents/silver.nix

    ../../base/core.nix

    ../../base/agents

    ../../base/claude
    ../../base/codex
    ../../base/testing

    ../../base/terminal/atuin.nix
    ../../base/terminal/fish.nix
    ../../base/terminal/kitty.nix
    ../../base/terminal/scripts.nix
    ../../base/terminal/tmux.nix
    ../../base/terminal/wezterm.nix
    ../../base/terminal/yazi

    ../../base/editor/neovim.nix

    ../../base/desktop/theming
    ../../darwin/desktop/hammerspoon
    ../../darwin/desktop/application-launcher
    ../../darwin/desktop/brave
    ../../base/desktop/fonts.nix
    ../../darwin/desktop/karabiner
    ../../darwin/desktop/keyboard-layout
    ../../darwin/desktop/maccy.nix
    ../../darwin/desktop/home-assistant-remote.nix

    ../../base/dev/devenv.nix
    ../../base/dev/git.nix
    ../../base/dev/glab.nix
    ../../base/dev/jira.nix
    ../../base/dev/lazygit.nix
    ../../base/dev/scripts.nix

    # ../../base/terminal/bad-apple.nix  # disabled on darwin: pulls latest.yt-dlp -> deno -> rusty-v8 (V8 build takes 30+ min on aarch64-darwin)
    ../../base/terminal/cbonsai.nix
    ../../base/terminal/cmatrix.nix

    ../../base/security/agenix.nix

    ../../base/network/tailscale-daemon.nix

    ../../base/media/obsidian
    ../../base/media/zathura

    "${inputs.private-config}/sb-toolkit"
  ]
  ++ lib.optionals rinPrivateConfigExists [
    "${privateConfigRoot}/machines/rin/clawde-pm.nix"
  ];
}
