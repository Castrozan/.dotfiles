{
  config,
  lib,
  pkgs,
  ...
}:
let
  inherit (config.home) homeDirectory;
  tailnetBindAddress = import ../tailnet-bind-address.nix { inherit lib; };
  stremioWebPort = "43212";
  stremioWebUrl = "http://${tailnetBindAddress}:${stremioWebPort}";
  stremioStreamingServerUrl = "http://${tailnetBindAddress}:11470/";
  stremioCometUrl = "http://${tailnetBindAddress}:43214";
  stremioGatewayPackageDirectory = ./scripts/stremio_gateway;
  stremioWeb = pkgs.fetchzip {
    url = "https://github.com/Stremio/stremio-web/releases/download/v5.0.0-beta.39/stremio-web.zip";
    hash = "sha256-8x7sDMh75Z1p6CV1lnmrOz8y+J/hz6ka0j26K0/G/l0=";
  };
in
{
  systemd.user = {
    services.stremio-web = {
      Unit = {
        Description = "Private Stremio Web and Prowlarr stream addon";
        After = [ "network-online.target" ];
        Wants = [ "network-online.target" ];
        StartLimitIntervalSec = 0;
      };

      Service = {
        ExecStart = "${pkgs.python3}/bin/python3 ${stremioGatewayPackageDirectory}";
        Restart = "on-failure";
        RestartSec = "5s";
        Environment = [
          "PYTHONUNBUFFERED=1"
          "STREMIO_BIND_ADDRESS=${tailnetBindAddress}"
          "STREMIO_WEB_PORT=${stremioWebPort}"
          "STREMIO_WEB_URL=${stremioWebUrl}"
          "STREMIO_PUBLIC_WEB_URL=https://stream.lucaszanoni.com"
          "STREMIO_WEB_ROOT=${stremioWeb}"
          "STREMIO_STREAMING_SERVER_URL=${stremioStreamingServerUrl}"
          "STREMIO_PUBLIC_ADDON_MANIFEST_URL=https://stream.lucaszanoni.com/comet/manifest.json"
          "STREMIO_TAILNET_ADDON_MANIFEST_URL=${stremioCometUrl}/manifest.json"
          "STREMIO_PROWLARR_URL=http://${tailnetBindAddress}:9696"
          "STREMIO_PROWLARR_CONFIG_FILE=${homeDirectory}/arr-stack/config/prowlarr/config.xml"
          "STREMIO_METADATA_URL=https://v3-cinemeta.strem.io"
        ];
      };

      Install.WantedBy = [ "default.target" ];
    };

    startServices = "sd-switch";
  };
}
