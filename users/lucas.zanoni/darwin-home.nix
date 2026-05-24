{ lib, inputs, ... }:
let
  privateConfigRoot = ../../private-config;
  macbookAlphaPrivateConfigExists = builtins.pathExists privateConfigRoot;
in
{
  imports = [
    ./pkgs.nix

    ./home/git.nix
    ./home/ssh.nix
    ./home/session-vars.nix
    ./home/clawde-silver.nix

    ../../home/core.nix

    ../../home/modules/agents

    ../../home/modules/claude
    ../../home/modules/codex

    ../../home/modules/terminal/atuin.nix
    ../../home/modules/terminal/fish.nix
    ../../home/modules/terminal/kitty.nix
    ../../home/modules/terminal/scripts.nix
    ../../home/modules/terminal/tmux.nix
    ../../home/modules/terminal/wezterm.nix
    ../../home/modules/terminal/yazi

    ../../home/modules/editor/neovim.nix
    ../../home/modules/editor/vscode/vscode.nix

    ../../home/modules/desktop/theming
    ../../home/darwin/desktop/aerospace.nix
    ../../home/darwin/desktop/application-launcher
    ../../home/darwin/desktop/brave
    ../../home/darwin/desktop/workspace-navigator
    ../../home/darwin/desktop/workspace-switcher-client
    ../../home/modules/desktop/fonts.nix
    ../../home/darwin/desktop/karabiner
    ../../home/darwin/desktop/keyboard-layout
    ../../home/darwin/desktop/maccy.nix
    ../../home/darwin/desktop/spaceman.nix
    ../../home/darwin/desktop/summon-browser
    ../../home/darwin/desktop/home-assistant-remote.nix

    ../../home/modules/dev/devenv.nix
    ../../home/modules/dev/git.nix
    ../../home/modules/dev/glab.nix
    ../../home/modules/dev/jira.nix
    ../../home/modules/dev/lazygit.nix
    ../../home/modules/dev/scripts.nix

    ../../home/modules/terminal/bad-apple.nix
    ../../home/modules/terminal/cbonsai.nix
    ../../home/modules/terminal/cmatrix.nix

    ../../home/modules/security/agenix.nix

    ../../home/modules/network/tailscale-daemon.nix

    ../../home/modules/media/obsidian
    ../../home/modules/media/zathura

    "${inputs.private-config}/sb-toolkit"
  ]
  ++ lib.optionals macbookAlphaPrivateConfigExists [
    "${privateConfigRoot}/machines/macbook-alpha/clawde-pm.nix"
  ];
}
