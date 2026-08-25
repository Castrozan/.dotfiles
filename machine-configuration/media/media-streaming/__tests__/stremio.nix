{
  helpers,
  lib,
  pkgs,
  ...
}:
let
  inherit (helpers) mkEvalCheck;
  testHomeDirectory = "/home/test-user";

  homeModule = import ../stremio-home-manager.nix {
    config.home.homeDirectory = testHomeDirectory;
    inherit lib pkgs;
  };
  webUnit = homeModule.systemd.user.services.stremio-web;
  webEnvironment = lib.concatStringsSep " " webUnit.Service.Environment;
  systemModule = import ../stremio-streaming-server-nixos.nix { inherit lib pkgs; };
  streamingUnit = systemModule.systemd.services.stremio-streaming-server;
  gatewaySource = builtins.readFile ../scripts/stremio_gateway/stremio_gateway.py;
  serverSource = builtins.readFile ../scripts/stremio_gateway/__main__.py;
in
{
  chise-stremio-web-is-tailnet-only = mkEvalCheck "chise-stremio-web-is-tailnet-only" (
    lib.hasInfix "STREMIO_BIND_ADDRESS=" webEnvironment
    && !(lib.hasInfix "STREMIO_BIND_ADDRESS=0.0.0.0" webEnvironment)
    && !(lib.hasInfix "funnel" (lib.toLower webEnvironment))
  ) "Stremio Web and its local addon must bind only the private tailnet address";

  chise-stremio-web-pins-official-build = mkEvalCheck "chise-stremio-web-pins-official-build" (
    lib.hasInfix "github.com/Stremio/stremio-web/releases/download/v5.0.0-beta.39" (
      builtins.readFile ../stremio-home-manager.nix
    )
    && webUnit.Install.WantedBy == [ "default.target" ]
  ) "Stremio Web must come from a pinned official release and start with the user session";

  chise-stremio-addon-keeps-prowlarr-key-at-runtime =
    mkEvalCheck "chise-stremio-addon-keeps-prowlarr-key-at-runtime"
      (
        lib.hasInfix "STREMIO_PROWLARR_CONFIG_FILE=${testHomeDirectory}/arr-stack/config/prowlarr/config.xml" webEnvironment
        && lib.hasInfix "read_prowlarr_api_key" serverSource
        && !(lib.hasInfix "runtime-secret" gatewaySource)
      )
      "the Stremio addon must read Prowlarr's API key from live state instead of placing it in the Nix store or browser";

  chise-stremio-streaming-server-is-pinned-and-private =
    mkEvalCheck "chise-stremio-streaming-server-is-pinned-and-private"
      (
        lib.hasInfix "stremio/server:v4.21.1@sha256:3dc145603defba397467b2a2aa2354be2da1f86585d4ab825a70bd72782f2ef4" streamingUnit.serviceConfig.ExecStart
        && lib.hasInfix "--publish " streamingUnit.serviceConfig.ExecStart
        && lib.hasInfix ":11470:11470" streamingUnit.serviceConfig.ExecStart
        && !(lib.hasInfix "0.0.0.0" streamingUnit.serviceConfig.ExecStart)
        && streamingUnit.wantedBy == [ "multi-user.target" ]
      )
      "the official streaming server must be digest-pinned, tailnet-bound and systemd-owned";
}
