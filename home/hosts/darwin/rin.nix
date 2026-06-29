{ lib, ... }:
let
  privateConfigRoot = ../../../private-config;
  rinPrivateConfigExists = builtins.pathExists privateConfigRoot;
in
{
  imports = [
    ../../darwin
  ]
  ++ lib.optionals rinPrivateConfigExists [
    "${privateConfigRoot}/machines/rin/clawde-agents"
  ]
  ++ lib.optional (builtins.pathExists ../../../private-config/machines/rin/cloudflare-tunnel-connector.nix) ../../../private-config/machines/rin/cloudflare-tunnel-connector.nix;

  custom.cockpitSessionBridge = {
    enable = true;
    tmuxEnumerationSocket = "";
    persistentSession.enable = false;
  };
}
