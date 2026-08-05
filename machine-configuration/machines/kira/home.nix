{ lib, ... }:
let
  privateConfigRoot = ../../../private-config;
  kiraPrivateConfigExists = builtins.pathExists privateConfigRoot;
in
{
  imports = [
    ../../../home/darwin

    ../../../home/base/dev/git-toggle-user.nix

    ../../../home/base/browser/firefox.nix

    ../../../home/base/editor/jetbrains-idea.nix
    ../../../home/base/editor/scripts.nix
    ../../../home/base/editor/zed-editor.nix

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
