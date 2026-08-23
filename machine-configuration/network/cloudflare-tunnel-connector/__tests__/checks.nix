{
  helpers,
  pkgs,
  lib,
  ...
}:
let
  inherit (helpers) mkEvalCheck;

  evalCloudflareTunnelConnector =
    connectorSettings:
    (lib.evalModules {
      modules = [
        ../cloudflare-tunnel-connector-home-manager.nix
        {
          options.launchd.agents = lib.mkOption {
            type = lib.types.attrs;
            default = { };
          };
          config._module.args.pkgs = pkgs;
          config.custom.cloudflareTunnelConnector = connectorSettings;
        }
      ];
    }).config;

  cloudflareTunnelConnectorTunnelId = "00000000-0000-0000-0000-000000000000";
  cloudflareTunnelConnectorCredentialsFile = "/Users/test/.secrets/kira-session-connector-credentials";
  cloudflareTunnelConnectorIngress = [
    {
      hostname = "kira-session-origin.lucaszanoni.com";
      localServiceUrl = "http://127.0.0.1:8787";
    }
    {
      hostname = "watch.lucaszanoni.com";
      localServiceUrl = "http://127.0.0.1:9443";
    }
  ];

  cloudflareTunnelConnectorDisabled = evalCloudflareTunnelConnector {
    enable = false;
  };

  cloudflareTunnelConnectorEnabled = evalCloudflareTunnelConnector {
    enable = true;
    tunnelId = cloudflareTunnelConnectorTunnelId;
    ingress = cloudflareTunnelConnectorIngress;
    credentialsFile = cloudflareTunnelConnectorCredentialsFile;
  };

  cloudflareTunnelConnectorEnabledProgramArguments =
    cloudflareTunnelConnectorEnabled.launchd.agents.cloudflare-tunnel-connector.config.ProgramArguments;

  expectedCloudflaredIngressConfiguration = pkgs.writeText "cloudflared.yml" (
    builtins.toJSON {
      tunnel = cloudflareTunnelConnectorTunnelId;
      "credentials-file" = cloudflareTunnelConnectorCredentialsFile;
      ingress =
        map (route: {
          inherit (route) hostname;
          service = route.localServiceUrl;
        }) cloudflareTunnelConnectorIngress
        ++ [ { service = "http_status:404"; } ];
    }
  );
in
{
  domain-darwin-cloudflare-tunnel-connector-disabled-publishes-nothing =
    mkEvalCheck "domain-darwin-cloudflare-tunnel-connector-disabled-publishes-nothing"
      (!(cloudflareTunnelConnectorDisabled.launchd.agents ? cloudflare-tunnel-connector))
      "a disabled darwin Cloudflare Tunnel connector must emit no launchd agent so a host that does not opt in publishes no public origin and the cockpit bridge stays reachable only over loopback";

  domain-darwin-cloudflare-tunnel-connector-enabled-runs-cloudflared =
    mkEvalCheck "domain-darwin-cloudflare-tunnel-connector-enabled-runs-cloudflared"
      (
        cloudflareTunnelConnectorEnabled.launchd.agents.cloudflare-tunnel-connector.enable
        && lib.elem "${pkgs.cloudflared}/bin/cloudflared" cloudflareTunnelConnectorEnabledProgramArguments
      )
      "an enabled darwin connector must run cloudflared under a launchd agent so the owner-only cockpit terminal reaches the loopback bridge over the named tunnel";

  domain-darwin-cloudflare-tunnel-connector-config-routes-declared-origins-to-loopback-with-agenix-credentials =
    mkEvalCheck
      "domain-darwin-cloudflare-tunnel-connector-config-routes-declared-origins-to-loopback-with-agenix-credentials"
      (lib.elem "--config=${expectedCloudflaredIngressConfiguration}" cloudflareTunnelConnectorEnabledProgramArguments)
      "the connector must run cloudflared with a config that registers the configured tunnelId, routes every declared ingress hostname to its loopback service, answers every other hostname with a 404, and reads its credentials from the agenix-provisioned path, so it exposes nothing else and keeps the account tag and tunnel secret out of the Nix store";
}
