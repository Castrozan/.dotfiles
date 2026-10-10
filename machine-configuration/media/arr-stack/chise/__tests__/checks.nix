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
      hostname = "suwayomi.lucaszanoni.com";
      proxyPort = 9452;
      upstreamPort = 4567;
      loginLocationRegexes = [ ];
    }
    {
      hostname = "readmeabook.lucaszanoni.com";
      proxyPort = 9454;
      upstreamPort = 3030;
      loginLocationRegexes = [ "^/api/auth/(local/login|admin/login|token/login|register)$" ];
    }
    {
      hostname = "audiobookshelf.lucaszanoni.com";
      proxyPort = 9455;
      upstreamPort = 13378;
      loginLocationRegexes = [ "^/login$" ];
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
          hostname = "stream.lucaszanoni.com";
          localServiceUrl = "http://127.0.0.1:9446";
        } cloudflareMediaIngress
      )
      "the owner-gated lucaszanoni.com media hostnames must reach their loopback proxies rather than the media containers directly";

  chise-arr-private-cloudflare-applications-complete =
    mkEvalCheck "chise-arr-private-cloudflare-applications-complete"
      privateCloudflareApplicationsAreDeclared
      "Miwayomi, Suwayomi, ReadMeABook, and Audiobookshelf must each have a dedicated owner-gated Cloudflare hostname routed through a loopback proxy to the existing tailnet-bound service";

  chise-arr-administration-applications-stay-off-cloudflare =
    mkEvalCheck "chise-arr-administration-applications-stay-off-cloudflare"
      (
        builtins.all (
          route:
          !(builtins.elem route.hostname [
            "radarr.lucaszanoni.com"
            "sonarr.lucaszanoni.com"
            "prowlarr.lucaszanoni.com"
            "bazarr.lucaszanoni.com"
            "qbittorrent.lucaszanoni.com"
          ])
        ) cloudflareMediaIngress
        && builtins.all (
          origin:
          !(builtins.elem origin.listenPort [
            9448
            9449
            9450
            9451
            9453
          ])
        ) cloudflareProxyOrigins
      )
      "Radarr, Sonarr, Prowlarr, Bazarr, and qBittorrent must keep their existing services without Cloudflare ingress or public login proxies";
}
