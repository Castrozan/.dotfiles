{
  config,
  lib,
  pkgs,
  ...
}:
let
  cloudflareTunnelConnectorConfig = config.custom.cloudflareTunnelConnector;

  cloudflaredIngressConfiguration = pkgs.writeText "cloudflared.yml" (
    builtins.toJSON {
      tunnel = cloudflareTunnelConnectorConfig.tunnelId;
      "credentials-file" = cloudflareTunnelConnectorConfig.credentialsFile;
      ingress = [
        {
          hostname = cloudflareTunnelConnectorConfig.ingressHostname;
          service = cloudflareTunnelConnectorConfig.localServiceUrl;
        }
        { service = "http_status:404"; }
      ];
    }
  );
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
      description = "Path to the decrypted Cloudflare Tunnel connector credentials JSON, provisioned through home-manager agenix so the account tag and tunnel secret never land in the Nix store.";
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
    launchd.agents.cloudflare-tunnel-connector = {
      enable = true;
      config = {
        Label = "com.dotfiles.cloudflare-tunnel-connector";
        ProgramArguments = [
          "${pkgs.cloudflared}/bin/cloudflared"
          "tunnel"
          "--config=${cloudflaredIngressConfiguration}"
          "--no-autoupdate"
          "run"
        ];
        EnvironmentVariables = {
          TUNNEL_EDGE_IP_VERSION = "4";
        };
        KeepAlive = true;
        RunAtLoad = true;
        StandardOutPath = "/tmp/cloudflare-tunnel-connector.log";
        StandardErrorPath = "/tmp/cloudflare-tunnel-connector.log";
      };
    };
  };
}
