{ lib, ... }:
let
  privateConfigRoot = ../../../private-config;
  rinPrivateConfigExists = builtins.pathExists privateConfigRoot;
in
{
  imports = [
    ../shared-darwin-home-manager.nix
  ]
  ++ lib.optionals rinPrivateConfigExists [
    "${privateConfigRoot}/machines/rin/clawde-agents"
    "${privateConfigRoot}/machines/rin/claude/mcd-ca-workspace-credentials.nix"
  ]
  ++ lib.optional (builtins.pathExists ../../../private-config/machines/rin/cloudflare-tunnel-connector.nix) ../../../private-config/machines/rin/cloudflare-tunnel-connector.nix;

  custom.cockpitSessionBridge = {
    enable = true;
    tmuxEnumerationSocket = "";
    persistentSession.enable = false;
  };
}
