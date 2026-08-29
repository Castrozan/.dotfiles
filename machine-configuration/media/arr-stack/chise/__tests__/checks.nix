{
  helpers,
  lib,
  self,
  ...
}:
let
  inherit (helpers) mkEvalCheck;
  nixosCfg = self.nixosConfigurations.chise.config;
  cloudflareMediaIngress = nixosCfg.custom.cloudflareTunnelConnector.ingress;
  cloudflareProxyOrigins = nixosCfg.custom.arrMediaLoginRateLimitProxy.origins;
  chiseTailnetBindAddress = import ../../../tailnet-bind-address.nix { inherit lib; };
  privateCloudflareApplicationExpectations = [
    {
      hostname = "anime.lucaszanoni.com";
      proxyPort = 9447;
      upstreamPort = 4568;
      loginLocationRegexes = [ ];
    }
    {
      hostname = "radarr.lucaszanoni.com";
      proxyPort = 9448;
      upstreamPort = 7878;
      loginLocationRegexes = [ "^/login$" ];
    }
    {
      hostname = "sonarr.lucaszanoni.com";
      proxyPort = 9449;
      upstreamPort = 8989;
      loginLocationRegexes = [ "^/login$" ];
    }
    {
      hostname = "prowlarr.lucaszanoni.com";
      proxyPort = 9450;
      upstreamPort = 9696;
      loginLocationRegexes = [ "^/login$" ];
    }
    {
      hostname = "bazarr.lucaszanoni.com";
      proxyPort = 9451;
      upstreamPort = 6767;
      loginLocationRegexes = [ "^/login$" ];
    }
    {
      hostname = "suwayomi.lucaszanoni.com";
      proxyPort = 9452;
      upstreamPort = 4567;
      loginLocationRegexes = [ ];
    }
    {
      hostname = "qbittorrent.lucaszanoni.com";
      proxyPort = 9453;
      upstreamPort = 8080;
      loginLocationRegexes = [ "^/api/v2/auth/login$" ];
    }
  ];
  privateCloudflareApplicationsAreDeclared = builtins.all (
    application:
    builtins.elem {
      inherit (application) hostname;
      localServiceUrl = "http://127.0.0.1:${toString application.proxyPort}";
    } cloudflareMediaIngress
    && builtins.elem {
      listenPort = application.proxyPort;
      upstreamUrl = "http://${chiseTailnetBindAddress}:${toString application.upstreamPort}";
      inherit (application) loginLocationRegexes;
    } cloudflareProxyOrigins
  ) privateCloudflareApplicationExpectations;
in
(import ./chise-arr-stack-host-integration.nix { inherit lib mkEvalCheck nixosCfg; })
// {
  chise-arr-media-cloudflare-tunnel-targets-ratelimit-proxy-not-container =
    mkEvalCheck "chise-arr-media-cloudflare-tunnel-targets-ratelimit-proxy-not-container"
      (
        builtins.elem {
          hostname = "watch.lucaszanoni.com";
          localServiceUrl = "http://127.0.0.1:9443";
        } cloudflareMediaIngress
        && builtins.elem {
          hostname = "request.lucaszanoni.com";
          localServiceUrl = "http://127.0.0.1:9444";
        } cloudflareMediaIngress
        && builtins.elem {
          hostname = "read.lucaszanoni.com";
          localServiceUrl = "http://127.0.0.1:9445";
        } cloudflareMediaIngress
        && builtins.elem {
          hostname = "stream.lucaszanoni.com";
          localServiceUrl = "http://127.0.0.1:9446";
        } cloudflareMediaIngress
      )
      "the owner-gated lucaszanoni.com media hostnames must reach their loopback proxies rather than the media containers directly";

  chise-arr-private-cloudflare-applications-complete =
    mkEvalCheck "chise-arr-private-cloudflare-applications-complete"
      privateCloudflareApplicationsAreDeclared
      "Miwayomi, Radarr, Sonarr, Prowlarr, Bazarr, Suwayomi, and qBittorrent must each have a dedicated owner-gated Cloudflare hostname routed through a loopback proxy to the existing tailnet-bound service";
}
