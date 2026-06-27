{ lib, ... }:
let
  privateConfigRoot = ../../../private-config;
  kiraPrivateConfigExists = builtins.pathExists privateConfigRoot;
in
{
  imports = [
    ../../darwin

    ../../base/dev/git-toggle-user.nix

    ../../base/opencode
    ../../base/opencode/private.nix

    ../../base/browser/firefox.nix

    ../../base/editor/jetbrains-idea.nix
    ../../base/editor/scripts.nix
    ../../base/editor/zed-editor.nix

    ../../base/dev/aws.nix
    ../../base/dev/bitwarden-cli.nix
    ../../base/dev/google-workspace-cli.nix
    ../../base/dev/infisical.nix
    ../../base/dev/mcporter.nix
    ../../base/dev/mongodb-atlas-cli.nix
    ../../base/dev/ralph-tui.nix
    ../../base/dev/temporal.nix
    ../../base/dev/tuisvn.nix
  ]
  ++ lib.optionals kiraPrivateConfigExists [
    "${privateConfigRoot}/machines/kira/clawde-agents"
  ]
  ++ lib.optional (builtins.pathExists ../../../private-config/machines/kira/jarvis-connector.nix) ../../../private-config/machines/kira/jarvis-connector.nix;

  custom.cockpitSessionBridge.enable = true;
}
