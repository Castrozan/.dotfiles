{ lib, inputs, ... }:
let
  privateConfigRoot = ../../../private-config;
  macbookBetaClawdePmPath = "${toString privateConfigRoot}/machines/macbook-beta/clawde-pm.nix";
  macbookBetaClawdePmExists = builtins.pathExists macbookBetaClawdePmPath;
in
{
  imports = [
    ../pkgs.nix

    ../home/git.nix
    ../home/ssh.nix
    ../home/session-vars.nix
    ../home/clawde-silver.nix

    ../../../home/base/core.nix

    ../../../home/base/agents

    ../../../home/base/claude
    ../../../home/base/codex

    ../../../home/base/terminal/atuin.nix
    ../../../home/base/terminal/fish.nix
    ../../../home/base/terminal/kitty.nix
    ../../../home/base/terminal/scripts.nix
    ../../../home/base/terminal/tmux.nix
    ../../../home/base/terminal/wezterm.nix
    ../../../home/base/terminal/yazi

    ../../../home/base/editor/neovim.nix
    ../../../home/base/editor/vscode/vscode.nix

    ../../../home/base/desktop/theming
    ../../../home/darwin/desktop/aerospace.nix
    ../../../home/darwin/desktop/application-launcher
    ../../../home/darwin/desktop/brave
    ../../../home/darwin/desktop/workspace-navigator
    ../../../home/darwin/desktop/workspace-switcher-client
    ../../../home/base/desktop/fonts.nix
    ../../../home/darwin/desktop/karabiner
    ../../../home/darwin/desktop/keyboard-layout
    ../../../home/darwin/desktop/maccy.nix
    ../../../home/darwin/desktop/spaceman.nix
    ../../../home/darwin/desktop/summon-browser
    ../../../home/darwin/desktop/home-assistant-remote.nix

    ../../../home/base/dev/devenv.nix
    ../../../home/base/dev/git.nix
    ../../../home/base/dev/glab.nix
    ../../../home/base/dev/jira.nix
    ../../../home/base/dev/lazygit.nix
    ../../../home/base/dev/scripts.nix

    ../../../home/base/terminal/bad-apple.nix
    ../../../home/base/terminal/cbonsai.nix
    ../../../home/base/terminal/cmatrix.nix

    ../../../home/base/security/agenix.nix

    ../../../home/base/network/tailscale-daemon.nix

    ../../../home/base/media/obsidian
    ../../../home/base/media/zathura

    "${inputs.private-config}/sb-toolkit"
  ]
  ++ lib.optionals macbookBetaClawdePmExists [
    macbookBetaClawdePmPath
  ];
}
