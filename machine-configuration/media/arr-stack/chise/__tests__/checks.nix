{
  helpers,
  lib,
  self,
  ...
}:
let
  inherit (helpers) mkEvalCheck;
  nixosCfg = self.nixosConfigurations.chise.config;
  secretNames = [
    "arr-bazarr-password"
    "arr-prowlarr-password"
    "arr-qbittorrent-password"
    "arr-radarr-password"
    "arr-samaritano-indexer-apikey"
    "arr-sonarr-password"
    "jellyfin-admin-api-key"
    "jellyseerr-smtp-app-password"
    "kavita-admin-api-key"
  ];
  chiseArrStackConfiguration = import ../chise-arr-stack-nixos.nix {
    inherit lib;
    config.age.secrets = builtins.listToAttrs (
      map (secretName: {
        name = secretName;
        value.path = "/run/agenix/${secretName}";
      }) secretNames
    );
  };
  cloudflareMediaIngress =
    chiseArrStackConfiguration.custom.cloudflareTunnelConnector.ingress.content;
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
      )
      "the owner-gated lucaszanoni.com media hostnames must reach the existing loopback login limiter rather than the Jellyfin or Jellyseerr container ports directly";
}
