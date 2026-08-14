{ lib, ... }:
let
  privateConfigRoot = ../../../private-configuration;
  kiraPrivateConfigExists = builtins.pathExists privateConfigRoot;
in
{
  imports = [
    ../shared-darwin-home-manager.nix

    ../../../machine-configuration/development/version-control/git-toggle-user-home-manager.nix

    ../../../machine-configuration/browsers/firefox/firefox-home-manager.nix

    ../../../machine-configuration/editors/jetbrains-idea/jetbrains-idea-home-manager.nix
    ../../../machine-configuration/editors/editor-command-packages-home-manager.nix
    ../../../machine-configuration/editors/zed/zed-home-manager.nix

    ../../../machine-configuration/development/cloud-services/aws-home-manager.nix
    ../../../machine-configuration/development/cloud-services/bitwarden-cli-home-manager.nix
    ../../../machine-configuration/development/cloud-services/infisical-home-manager.nix
    ../../../machine-configuration/development/model-context-protocol/mcporter-home-manager.nix
    ../../../machine-configuration/development/database-tools/mongodb-atlas-cli-home-manager.nix
    ../../../machine-configuration/development/development-environments/ralph-tui-home-manager.nix
    ../../../machine-configuration/development/development-environments/temporal-home-manager.nix
    ../../../machine-configuration/development/version-control/tuisvn-home-manager.nix
  ]
  ++ lib.optionals kiraPrivateConfigExists [
    "${privateConfigRoot}/machines/kira/clawde-agents"
    "${privateConfigRoot}/machines/kira/scheduled-tasks"
  ]
  ++ lib.optional (builtins.pathExists ../../../private-configuration/machines/kira/cloudflare-tunnel-connector.nix) ../../../private-configuration/machines/kira/cloudflare-tunnel-connector.nix;

  custom.cockpitSessionBridge = {
    enable = true;
    tmuxEnumerationSocket = "";
    tmuxMutationSocket = "";
    persistentSession.enable = false;
  };
}
