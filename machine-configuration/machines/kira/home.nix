{ lib, ... }:
let
  privateConfigRoot = ../../../private-config;
  kiraPrivateConfigExists = builtins.pathExists privateConfigRoot;
in
{
  imports = [
    ../../../home/darwin

    ../../../home/base/dev/git-toggle-user.nix

    ../../../machine-configuration/browsers/firefox/firefox-home-manager.nix

    ../../../machine-configuration/editors/jetbrains-idea/jetbrains-idea-home-manager.nix
    ../../../machine-configuration/editors/editor-command-packages-home-manager.nix
    ../../../machine-configuration/editors/zed/zed-home-manager.nix

    ../../../home/base/dev/aws.nix
    ../../../home/base/dev/bitwarden-cli.nix
    ../../../home/base/dev/google-workspace-cli
    ../../../home/base/dev/infisical.nix
    ../../../home/base/dev/mcporter.nix
    ../../../home/base/dev/mongodb-atlas-cli.nix
    ../../../home/base/dev/ralph-tui.nix
    ../../../home/base/dev/temporal.nix
    ../../../home/base/dev/tuisvn.nix
  ]
  ++ lib.optionals kiraPrivateConfigExists [
    "${privateConfigRoot}/machines/kira/clawde-agents"
    "${privateConfigRoot}/machines/kira/scheduled-tasks"
  ]
  ++ lib.optional (builtins.pathExists ../../../private-config/machines/kira/cloudflare-tunnel-connector.nix) ../../../private-config/machines/kira/cloudflare-tunnel-connector.nix;

  custom.cockpitSessionBridge = {
    enable = true;
    tmuxEnumerationSocket = "";
    tmuxMutationSocket = "";
    persistentSession.enable = false;
  };
}
