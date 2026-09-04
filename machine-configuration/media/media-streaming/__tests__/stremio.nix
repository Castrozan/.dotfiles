{
  helpers,
  lib,
  pkgs,
  ...
}:
let
  inherit (helpers) mkEvalCheck;
  testHomeDirectory = "/home/test-user";
  tailnetBindAddress = import ../../tailnet-bind-address.nix { inherit lib; };

  homeModule = import ../stremio-home-manager.nix {
    config.home.homeDirectory = testHomeDirectory;
    inherit lib pkgs;
  };
  webUnit = homeModule.systemd.user.services.stremio-web;
  webEnvironment = lib.concatStringsSep " " webUnit.Service.Environment;
  streamCacheDirectory = "/mnt/media-drive/stremio-cache";
  systemModule = import ../stremio-streaming-server-nixos.nix {
    config.custom.stremioStreamingServer.streamCacheDirectory = streamCacheDirectory;
    inherit lib pkgs;
  };
  streamingUnit = systemModule.config.systemd.services.stremio-streaming-server;
  cometModule = import ../stremio-comet-nixos.nix {
    config.users.users.zanoni.home = testHomeDirectory;
    inherit lib pkgs;
  };
  cometUnit = cometModule.systemd.services.stremio-comet;
  publicOriginModule = import ../stremio-public-origin-nixos.nix { inherit lib; };
  publicOriginNginx = publicOriginModule.services.nginx;
  publicOriginVirtualHost = publicOriginNginx.virtualHosts.stremio-public-origin;
  publicOriginHttpConfig = publicOriginNginx.appendHttpConfig.content;
  gatewaySource = builtins.readFile ../scripts/stremio_gateway/prowlarr_stream_provider.py;
  cometAdapterSource = builtins.readFile ../scripts/stremio_gateway/comet_stream_adapter.py;
  managedProfileSource = lib.concatStrings [
    (builtins.readFile ../scripts/stremio_gateway/managed_profile.js)
    (builtins.readFile ../scripts/stremio_gateway/managed_profile.json)
  ];
  managedServiceWorkerSource = builtins.readFile ../scripts/stremio_gateway/managed_service_worker.js;
  serverSource = builtins.readFile ../scripts/stremio_gateway/__main__.py;
  cometEnvironmentSource = builtins.readFile ../scripts/stremio_comet_environment.py;
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

  chise-stremio-web-manages-private-addons =
    mkEvalCheck "chise-stremio-web-manages-private-addons"
      (
        lib.hasInfix "STREMIO_PUBLIC_WEB_URL=https://stream.lucaszanoni.com" webEnvironment
        && lib.hasInfix "STREMIO_COMET_URL=http://${tailnetBindAddress}:43214" webEnvironment
        && lib.hasInfix "tracker:" cometAdapterSource
        && lib.hasInfix "dht:" cometAdapterSource
        && lib.hasInfix "com.lucaszanoni.prowlarr-streams" managedProfileSource
        && lib.hasInfix "stremio.comet.fast" managedProfileSource
        && lib.hasInfix "addonsLocked: true" managedProfileSource
        && lib.hasInfix "https://v3-cinemeta.strem.io/manifest.json" managedProfileSource
        && lib.hasInfix "schema_version" managedProfileSource
        && lib.hasInfix "/managed-profile.js" serverSource
        && lib.hasInfix "/service-worker.js" serverSource
        && lib.hasInfix "caches.delete" managedServiceWorkerSource
        && lib.hasInfix "self.clients.claim()" managedServiceWorkerSource
        && !(lib.hasInfix "/setup" serverSource)
      )
      "ordinary Stremio launches must reconcile the Nix-managed private addons before the upstream application starts";

  chise-stremio-public-origin-is-loopback-only =
    mkEvalCheck "chise-stremio-public-origin-is-loopback-only"
      (
        publicOriginVirtualHost.listen == [
          {
            addr = "127.0.0.1";
            port = 9446;
            ssl = false;
          }
        ]
        && publicOriginVirtualHost.locations."/".proxyPass == "http://${tailnetBindAddress}:43212"
        && publicOriginVirtualHost.locations."/server/".proxyPass == "http://${tailnetBindAddress}:11470/"
        &&
          publicOriginVirtualHost.locations."/comet/".proxyPass == "http://${tailnetBindAddress}:43212/comet/"
      )
      "the public Stremio origin must expose one loopback listener to cloudflared and keep every upstream service on the tailnet";

  chise-stremio-comet-is-pinned-private-and-bounded =
    mkEvalCheck "chise-stremio-comet-is-pinned-private-and-bounded"
      (
        lib.hasInfix "g0ldyy/comet@sha256:dca62133336e02784d02aaad861381820674d1c8e3e98a03797610b81ee4defe" cometUnit.serviceConfig.ExecStart
        && lib.hasInfix "--network host" cometUnit.serviceConfig.ExecStart
        && lib.hasInfix "--dns 127.0.0.53" cometUnit.serviceConfig.ExecStart
        && lib.hasInfix "--env FASTAPI_HOST=${tailnetBindAddress}" cometUnit.serviceConfig.ExecStart
        && lib.hasInfix "--memory 1g" cometUnit.serviceConfig.ExecStart
        && lib.hasInfix "--cpus 2" cometUnit.serviceConfig.ExecStart
        && lib.hasInfix "urllib.request.urlopen('http://${tailnetBindAddress}:43214/health', timeout=5)" cometUnit.serviceConfig.ExecStart
        && lib.hasInfix "--health-start-period 90s" cometUnit.serviceConfig.ExecStart
        && lib.hasInfix "--env INDEXER_MANAGER_TIMEOUT=15" cometUnit.serviceConfig.ExecStart
        && lib.hasInfix "--env GET_TORRENT_TIMEOUT=10" cometUnit.serviceConfig.ExecStart
        && lib.hasInfix "--env 'PROWLARR_INDEXERS=[]'" cometUnit.serviceConfig.ExecStart
        && lib.hasInfix "--env 'INDEXER_LANGUAGES=[\"pt\"]'" cometUnit.serviceConfig.ExecStart
        && lib.hasInfix "--env-file /run/stremio-comet/prowlarr.env" cometUnit.serviceConfig.ExecStart
        && lib.hasInfix "${testHomeDirectory}/arr-stack/config/prowlarr/config.xml" (
          lib.concatStringsSep " " cometUnit.serviceConfig.ExecStartPre
        )
        && lib.hasInfix "PROWLARR_API_KEY" cometEnvironmentSource
        && !(lib.hasInfix "PROWLARR_API_KEY=" cometUnit.serviceConfig.ExecStart)
        && cometUnit.wantedBy == [ "multi-user.target" ]
      )
      "Comet must be digest-pinned, tailnet-bound, resource-bounded and receive the live Prowlarr key outside the Nix store";

  chise-stremio-public-origin-rewrites-hls-media-url =
    mkEvalCheck "chise-stremio-public-origin-rewrites-hls-media-url"
      (
        lib.hasInfix "stream[.]lucaszanoni[.]com%2fserver" publicOriginHttpConfig
        && lib.hasInfix "127.0.0.1%3A11470" publicOriginHttpConfig
        && publicOriginVirtualHost.locations."/hlsv2/".proxyPass == "http://${tailnetBindAddress}:11470"
        &&
          lib.hasInfix "set $args $stremioInternalHlsArguments;"
            publicOriginVirtualHost.locations."/hlsv2/".extraConfig
      )
      "the public Stremio HLS proxy must replace its recursive public media URL with the streaming server's own loopback URL before probing and segmenting";

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
        && lib.hasInfix "--dns 1.1.1.1" streamingUnit.serviceConfig.ExecStart
        && lib.hasInfix "--dns 8.8.8.8" streamingUnit.serviceConfig.ExecStart
        && !(lib.hasInfix "0.0.0.0" streamingUnit.serviceConfig.ExecStart)
        && streamingUnit.wantedBy == [ "multi-user.target" ]
      )
      "the official streaming server must be digest-pinned, tailnet-bound, systemd-owned and able to resolve public torrent trackers";

  chise-stremio-streaming-server-keeps-its-stream-cache-on-the-media-drive =
    mkEvalCheck "chise-stremio-streaming-server-keeps-its-stream-cache-on-the-media-drive"
      (
        lib.hasInfix "--volume ${streamCacheDirectory}:/root/.stremio-server/stremio-cache" streamingUnit.serviceConfig.ExecStart
        && lib.hasInfix "--volume /var/lib/stremio-streaming-server:/root/.stremio-server" streamingUnit.serviceConfig.ExecStart
        && streamingUnit.unitConfig.RequiresMountsFor == [ streamCacheDirectory ]
      )
      "the stream cache is the only media the streaming server writes and it must land on the configured drive with the unit waiting for that mount, while settings stay in the systemd state directory; a cache back on the root disk is what filled it to 95%";
}
