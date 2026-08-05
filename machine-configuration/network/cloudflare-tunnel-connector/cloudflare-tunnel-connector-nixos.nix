{
  config,
  lib,
  ...
}:
let
  cloudflareTunnelConnectorConfig = config.custom.cloudflareTunnelConnector;
in
{
  options.custom.cloudflareTunnelConnector = {
    enable = lib.mkEnableOption "the Cloudflare Tunnel connector that publishes a single loopback-only origin to the Cloudflare edge so the owner-only cockpit Internal terminal reaches the Jarvis session bridge without opening any inbound firewall port";

    tunnelId = lib.mkOption {
      type = lib.types.str;
      default = "";
      description = "Cloudflare Tunnel UUID this connector runs, recorded when the named tunnel is provisioned and stored alongside the connector credentials.";
    };

    credentialsFile = lib.mkOption {
      type = lib.types.str;
      default = "";
      description = "Path to the decrypted Cloudflare Tunnel connector credentials JSON, provisioned through agenix so the account tag and tunnel secret never land in the Nix store.";
    };

    ingressHostname = lib.mkOption {
      type = lib.types.str;
      default = "";
      description = "Public hostname the Cloudflare edge routes through this tunnel; every other hostname is answered with a 404 so the connector exposes nothing beyond the single Jarvis origin.";
    };

    localServiceUrl = lib.mkOption {
      type = lib.types.str;
      default = "http://127.0.0.1:8787";
      description = "Loopback URL of the co-located Jarvis session bridge the tunnel forwards the single published hostname to.";
    };
  };

  config = lib.mkIf cloudflareTunnelConnectorConfig.enable {
    services.cloudflared = {
      enable = true;
      tunnels.${cloudflareTunnelConnectorConfig.tunnelId} = {
        inherit (cloudflareTunnelConnectorConfig) credentialsFile;
        default = "http_status:404";
        ingress = {
          ${cloudflareTunnelConnectorConfig.ingressHostname} =
            cloudflareTunnelConnectorConfig.localServiceUrl;
        };
      };
    };
  };
}
