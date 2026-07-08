{
  config,
  lib,
  ...
}:
let
  arrMediaLoginRateLimitProxyConfig = config.custom.arrMediaLoginRateLimitProxy;

  originSubmodule = lib.types.submodule {
    options = {
      listenPort = lib.mkOption {
        type = lib.types.port;
        description = "Loopback port this proxy listens on for one media origin; the Tailscale Funnel targets this port instead of the container so every public request passes through the rate limiter first.";
      };

      upstreamUrl = lib.mkOption {
        type = lib.types.str;
        description = "Loopback URL of the container this origin proxies to, e.g. http://127.0.0.1:8096 for Jellyfin.";
      };

      loginLocationRegexes = lib.mkOption {
        type = lib.types.listOf lib.types.str;
        default = [ ];
        description = "Case-insensitive nginx location regexes for this origin's authentication endpoints; only these paths carry the strict per-client-IP login rate limit, so media streaming stays unthrottled.";
      };
    };
  };

  commonProxyExtraConfig = ''
    proxy_set_header X-Forwarded-Proto https;
    proxy_buffering off;
    proxy_read_timeout 3600s;
    proxy_send_timeout 3600s;
  '';

  loginLocationExtraConfig = ''
    limit_req zone=arrMediaLogin burst=${toString arrMediaLoginRateLimitProxyConfig.loginBurst} nodelay;
    limit_req_status 429;
  '';

  makeLoginLocation = upstreamUrl: regex: {
    name = "~* ${regex}";
    value = {
      proxyPass = upstreamUrl;
      proxyWebsockets = false;
      extraConfig = loginLocationExtraConfig + commonProxyExtraConfig;
    };
  };

  makeOriginVirtualHost = origin: {
    name = "arr-media-ratelimit-origin-${toString origin.listenPort}";
    value = {
      listen = [
        {
          addr = "127.0.0.1";
          port = origin.listenPort;
          ssl = false;
        }
      ];
      locations = {
        "/" = {
          proxyPass = origin.upstreamUrl;
          proxyWebsockets = true;
          extraConfig = ''
            limit_conn arrMediaConnections ${toString arrMediaLoginRateLimitProxyConfig.maxConnectionsPerClient};
          ''
          + commonProxyExtraConfig;
        };
      }
      // lib.listToAttrs (map (makeLoginLocation origin.upstreamUrl) origin.loginLocationRegexes);
    };
  };
in
{
  options.custom.arrMediaLoginRateLimitProxy = {
    enable = lib.mkEnableOption "a loopback nginx reverse proxy in front of the funnel-exposed media origins that rate-limits their login endpoints per real client IP, recovered from the Tailscale Funnel's X-Forwarded-For header, so a credential brute force or volumetric login flood is throttled before it reaches the loginless containers";

    loginRequestsPerMinute = lib.mkOption {
      type = lib.types.int;
      default = 15;
      description = "Sustained login attempts allowed per real client IP per minute before the proxy answers 429; the funnel hides client IPs from the host firewall, so this L7 limit is the enforcement point fail2ban cannot be.";
    };

    loginBurst = lib.mkOption {
      type = lib.types.int;
      default = 10;
      description = "Momentary burst of login attempts a single client IP may spend before the sustained per-minute rate applies.";
    };

    maxConnectionsPerClient = lib.mkOption {
      type = lib.types.int;
      default = 50;
      description = "Concurrent connections a single real client IP may hold open across an origin, blunting a volumetric connection flood without throttling the many short requests normal media streaming makes.";
    };

    origins = lib.mkOption {
      type = lib.types.listOf originSubmodule;
      default = [ ];
      description = "The funnel-exposed media origins fronted by the rate-limiting proxy, each pinning a loopback listen port to a container upstream and its login endpoint regexes.";
    };
  };

  config = lib.mkIf arrMediaLoginRateLimitProxyConfig.enable {
    services.nginx = {
      enable = true;
      recommendedProxySettings = true;
      recommendedOptimisation = true;
      clientMaxBodySize = "512m";
      appendHttpConfig = ''
        set_real_ip_from 127.0.0.1;
        real_ip_header X-Forwarded-For;
        map $remote_addr $arrMediaRateLimitKey {
          default $remote_addr;
          "~^(?<ipv4address>[0-9]+\.[0-9]+\.[0-9]+\.[0-9]+)$" $ipv4address;
          "~*^(?<ipv6prefix>[0-9a-f]+:[0-9a-f]+:[0-9a-f]+:[0-9a-f]+):" "$ipv6prefix::";
        }
        limit_req_zone $arrMediaRateLimitKey zone=arrMediaLogin:10m rate=${toString arrMediaLoginRateLimitProxyConfig.loginRequestsPerMinute}r/m;
        limit_conn_zone $arrMediaRateLimitKey zone=arrMediaConnections:10m;
      '';
      virtualHosts = lib.listToAttrs (
        map makeOriginVirtualHost arrMediaLoginRateLimitProxyConfig.origins
      );
    };
  };
}
