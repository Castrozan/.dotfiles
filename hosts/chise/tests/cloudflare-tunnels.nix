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

  evalCloudflareTunnelConnector =
    connectorSettings:
    (lib.evalModules {
      modules = [
        ../../../nixos/modules/cloudflare-tunnel-connector
        {
          options.services.cloudflared = lib.mkOption {
            type = lib.types.attrs;
            default = { };
          };
          config.custom.cloudflareTunnelConnector = connectorSettings;
        }
      ];
    }).config;

  cloudflareTunnelConnectorTunnelId = "00000000-0000-0000-0000-000000000000";

  cloudflareTunnelConnectorDisabled = evalCloudflareTunnelConnector {
    enable = false;
  };

  cloudflareTunnelConnectorEnabled = evalCloudflareTunnelConnector {
    enable = true;
    tunnelId = cloudflareTunnelConnectorTunnelId;
    ingressHostname = "jarvis-session-origin.lucaszanoni.com";
    credentialsFile = "/run/agenix/jarvis-session-connector-credentials";
  };

  cloudflareTunnelConnectorEnabledTunnel =
    cloudflareTunnelConnectorEnabled.services.cloudflared.tunnels.${cloudflareTunnelConnectorTunnelId};

  evalJellyseerrPublicRequestTunnel =
    tunnelSettings:
    (lib.evalModules {
      modules = [
        ../../../nixos/modules/jellyseerr-public-request-tunnel
        {
          options.services.cloudflared = lib.mkOption {
            type = lib.types.attrs;
            default = { };
          };
          config.custom.jellyseerrPublicRequestTunnel = tunnelSettings;
        }
      ];
    }).config;

  jellyseerrPublicRequestTunnelId = "11111111-1111-1111-1111-111111111111";

  jellyseerrPublicRequestTunnelDisabled = evalJellyseerrPublicRequestTunnel {
    enable = false;
  };

  jellyseerrPublicRequestTunnelEnabled = evalJellyseerrPublicRequestTunnel {
    enable = true;
    tunnelId = jellyseerrPublicRequestTunnelId;
    credentialsFile = "/run/agenix/jellyseerr-public-request-tunnel-credentials";
  };

  jellyseerrPublicRequestTunnelEnabledTunnel =
    jellyseerrPublicRequestTunnelEnabled.services.cloudflared.tunnels.${jellyseerrPublicRequestTunnelId};
in
{
  chise-cloudflare-tunnel-connector-disabled-publishes-nothing =
    mkEvalCheck "chise-cloudflare-tunnel-connector-disabled-publishes-nothing"
      (!(cloudflareTunnelConnectorDisabled.services.cloudflared.enable or false))
      "the Cloudflare Tunnel connector must publish no cloudflared service while disabled, so a host that does not opt in exposes no public origin and the Jarvis bridge stays reachable only over loopback";

  chise-cloudflare-tunnel-connector-enabled-turns-on-cloudflared =
    mkEvalCheck "chise-cloudflare-tunnel-connector-enabled-turns-on-cloudflared"
      cloudflareTunnelConnectorEnabled.services.cloudflared.enable
      "an enabled Cloudflare Tunnel connector must turn cloudflared on so the owner-only cockpit terminal reaches the Jarvis bridge over the named tunnel";

  chise-cloudflare-tunnel-connector-registers-tunnel-by-id =
    mkEvalCheck "chise-cloudflare-tunnel-connector-registers-tunnel-by-id"
      (builtins.hasAttr cloudflareTunnelConnectorTunnelId cloudflareTunnelConnectorEnabled.services.cloudflared.tunnels)
      "the connector must register the named tunnel under its configured tunnelId so cloudflared runs the provisioned tunnel rather than an empty default";

  chise-cloudflare-tunnel-connector-ingress-routes-origin-to-loopback =
    mkEvalCheck "chise-cloudflare-tunnel-connector-ingress-routes-origin-to-loopback"
      (
        cloudflareTunnelConnectorEnabledTunnel.ingress."jarvis-session-origin.lucaszanoni.com"
        == "http://127.0.0.1:8787"
      )
      "the connector must route only the single Jarvis origin hostname to the loopback bridge so it exposes nothing else from the host";

  chise-cloudflare-tunnel-connector-credentials-from-agenix =
    mkEvalCheck "chise-cloudflare-tunnel-connector-credentials-from-agenix"
      (
        cloudflareTunnelConnectorEnabledTunnel.credentialsFile
        == "/run/agenix/jarvis-session-connector-credentials"
      )
      "the connector must take its tunnel credentials from the agenix-provisioned path so the account tag and tunnel secret never enter the Nix store";

  chise-jellyseerr-public-request-tunnel-disabled-publishes-nothing =
    mkEvalCheck "chise-jellyseerr-public-request-tunnel-disabled-publishes-nothing"
      (!(jellyseerrPublicRequestTunnelDisabled.services.cloudflared.enable or false))
      "the Jellyseerr public request tunnel must publish no cloudflared service while disabled, so the request portal stays reachable only across the tailnet until the owner opts in at go-live";

  chise-jellyseerr-public-request-tunnel-enabled-turns-on-cloudflared =
    mkEvalCheck "chise-jellyseerr-public-request-tunnel-enabled-turns-on-cloudflared"
      jellyseerrPublicRequestTunnelEnabled.services.cloudflared.enable
      "an enabled Jellyseerr public request tunnel must turn cloudflared on so approved friends reach the request portal over the public hostname";

  chise-jellyseerr-public-request-tunnel-registers-tunnel-by-id =
    mkEvalCheck "chise-jellyseerr-public-request-tunnel-registers-tunnel-by-id"
      (builtins.hasAttr jellyseerrPublicRequestTunnelId jellyseerrPublicRequestTunnelEnabled.services.cloudflared.tunnels)
      "the tunnel must register under its configured tunnelId so cloudflared runs the provisioned media request tunnel rather than an empty default";

  chise-jellyseerr-public-request-tunnel-routes-hostname-to-jellyseerr =
    mkEvalCheck "chise-jellyseerr-public-request-tunnel-routes-hostname-to-jellyseerr"
      (
        jellyseerrPublicRequestTunnelEnabledTunnel.ingress."requests.lucaszanoni.com"
        == "http://100.94.11.81:5055"
      )
      "the tunnel must route only the public request hostname to the tailnet-bound Jellyseerr so it exposes the request portal and nothing else from the host";

  chise-jellyseerr-public-request-tunnel-catch-all-is-404 =
    mkEvalCheck "chise-jellyseerr-public-request-tunnel-catch-all-is-404"
      (jellyseerrPublicRequestTunnelEnabledTunnel.default == "http_status:404")
      "the tunnel must answer every non-request hostname with a 404 so Radarr, Sonarr, Prowlarr and qBittorrent stay tailnet-only and never leak through the public edge";

  chise-jellyseerr-public-request-tunnel-credentials-from-agenix =
    mkEvalCheck "chise-jellyseerr-public-request-tunnel-credentials-from-agenix"
      (
        jellyseerrPublicRequestTunnelEnabledTunnel.credentialsFile
        == "/run/agenix/jellyseerr-public-request-tunnel-credentials"
      )
      "the tunnel must take its credentials from the agenix-provisioned path so the account tag and tunnel secret never enter the Nix store";
}
