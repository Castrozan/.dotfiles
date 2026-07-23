{
  pkgs,
  lib,
}:
let
  helpers = import ../../../__tests__/nix-checks/helpers.nix {
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
}
