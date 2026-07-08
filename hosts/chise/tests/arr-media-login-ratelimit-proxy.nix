{
  pkgs,
  lib,
}:
let
  helpers = import ../../../tests/nix-checks/helpers.nix {
    inherit pkgs lib;
    inputs = { };
    nixpkgs-version = "25.11";
    home-version = "25.11";
  };
  inherit (helpers) mkEvalCheck;

  evalRateLimitProxy =
    settings:
    (lib.evalModules {
      modules = [
        ../../../nixos/modules/arr-media-login-ratelimit-proxy
        {
          options.services.nginx = lib.mkOption {
            type = lib.types.attrs;
            default = { };
          };
          config.custom.arrMediaLoginRateLimitProxy = settings;
        }
      ];
    }).config;

  rateLimitProxyDisabled = evalRateLimitProxy {
    enable = false;
  };

  rateLimitProxyEnabled = evalRateLimitProxy {
    enable = true;
    origins = [
      {
        listenPort = 9443;
        upstreamUrl = "http://127.0.0.1:8096";
        loginLocationRegexes = [ "^/Users/AuthenticateByName" ];
      }
      {
        listenPort = 9444;
        upstreamUrl = "http://127.0.0.1:5055";
        loginLocationRegexes = [ "^/api/v1/auth/(jellyfin|plex|local)" ];
      }
    ];
  };

  enabledNginx = rateLimitProxyEnabled.services.nginx;
  jellyfinOriginVirtualHost = enabledNginx.virtualHosts.arr-media-ratelimit-origin-9443;
  jellyfinLoginLocation = jellyfinOriginVirtualHost.locations."~* ^/Users/AuthenticateByName";
  jellyfinRootLocation = jellyfinOriginVirtualHost.locations."/";
in
{
  chise-arr-media-ratelimit-disabled-runs-no-nginx =
    mkEvalCheck "chise-arr-media-ratelimit-disabled-runs-no-nginx"
      (!(rateLimitProxyDisabled.services.nginx.enable or false))
      "the login rate-limit proxy must configure no nginx while disabled, so a host that does not opt in adds no reverse proxy in front of its media origins";

  chise-arr-media-ratelimit-enabled-turns-on-nginx =
    mkEvalCheck "chise-arr-media-ratelimit-enabled-turns-on-nginx" enabledNginx.enable
      "an enabled login rate-limit proxy must turn nginx on so the funnel has a rate-limiting hop to target instead of the loginless container directly";

  chise-arr-media-ratelimit-recovers-real-client-ip =
    mkEvalCheck "chise-arr-media-ratelimit-recovers-real-client-ip"
      (
        lib.hasInfix "set_real_ip_from 127.0.0.1" enabledNginx.appendHttpConfig
        && lib.hasInfix "real_ip_header X-Forwarded-For" enabledNginx.appendHttpConfig
      )
      "nginx must trust the loopback funnel hop and read the real client IP from X-Forwarded-For, or the per-IP login limit would key on 127.0.0.1 and throttle every user as one";

  chise-arr-media-ratelimit-defines-login-rate-zone =
    mkEvalCheck "chise-arr-media-ratelimit-defines-login-rate-zone"
      (
        lib.hasInfix "limit_req_zone $arrMediaRateLimitKey zone=arrMediaLogin" enabledNginx.appendHttpConfig
        && lib.hasInfix "limit_conn_zone $arrMediaRateLimitKey zone=arrMediaConnections" enabledNginx.appendHttpConfig
      )
      "nginx must define the login rate zone and the connection zone keyed on the masked client-prefix variable so both the brute-force and the volumetric-flood limits have shared memory to count against";

  chise-arr-media-ratelimit-key-masks-client-prefix =
    mkEvalCheck "chise-arr-media-ratelimit-key-masks-client-prefix"
      (
        lib.hasInfix "map $remote_addr $arrMediaRateLimitKey" enabledNginx.appendHttpConfig
        && lib.hasInfix "$ipv6prefix::" enabledNginx.appendHttpConfig
      )
      "the rate-limit key must mask the client address to a prefix (full IPv4, IPv6 /64) so an IPv6 client cannot rotate source addresses within its allocation to buy a fresh login budget per request and defeat the whole limiter";

  chise-arr-media-ratelimit-login-endpoint-is-limited =
    mkEvalCheck "chise-arr-media-ratelimit-login-endpoint-is-limited"
      (
        lib.hasInfix "limit_req zone=arrMediaLogin" jellyfinLoginLocation.extraConfig
        && lib.hasInfix "limit_req_status 429" jellyfinLoginLocation.extraConfig
      )
      "the Jellyfin AuthenticateByName location must carry the strict login rate limit and answer 429 when exceeded, since that endpoint is the credential-brute-force and PBKDF2 CPU-exhaustion vector";

  chise-arr-media-ratelimit-streaming-path-unthrottled-and-websocket =
    mkEvalCheck "chise-arr-media-ratelimit-streaming-path-unthrottled-and-websocket"
      (
        jellyfinRootLocation.proxyWebsockets
        && !(lib.hasInfix "limit_req zone=arrMediaLogin" jellyfinRootLocation.extraConfig)
        && lib.hasInfix "limit_conn arrMediaConnections" jellyfinRootLocation.extraConfig
      )
      "the catch-all location must proxy websockets and carry no login rate limit so media playback and real-time sync are untouched, while still capping concurrent connections per client against a flood";

  chise-arr-media-ratelimit-binds-loopback-only =
    mkEvalCheck "chise-arr-media-ratelimit-binds-loopback-only"
      (builtins.all (entry: entry.addr == "127.0.0.1") jellyfinOriginVirtualHost.listen)
      "every proxy origin must listen on 127.0.0.1 only so it is reachable through the Tailscale Funnel hop alone and never directly on the tailnet or LAN";
}
