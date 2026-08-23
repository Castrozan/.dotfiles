{
  config,
  lib,
  pkgs,
  ...
}:
let
  cloudflareTunnelConnectorConfig = config.custom.cloudflareTunnelConnector;
  ingressRouteSubmodule = lib.types.submodule {
    options = {
      hostname = lib.mkOption {
        type = lib.types.str;
        description = "Public hostname Cloudflare routes through the named tunnel.";
      };

      localServiceUrl = lib.mkOption {
        type = lib.types.str;
        description = "Loopback URL the connector serves for this hostname.";
      };
    };
  };

  cloudflaredIngressConfiguration = pkgs.writeText "cloudflared.yml" (
    builtins.toJSON {
      tunnel = cloudflareTunnelConnectorConfig.tunnelId;
      "credentials-file" = cloudflareTunnelConnectorConfig.credentialsFile;
      ingress =
        map (route: {
          inherit (route) hostname;
          service = route.localServiceUrl;
        }) cloudflareTunnelConnectorConfig.ingress
        ++ [ { service = "http_status:404"; } ];
    }
  );
in
{
  options.custom.cloudflareTunnelConnector = {
    enable = lib.mkEnableOption "the named Cloudflare Tunnel connector that publishes explicit loopback-only ingress routes without opening an inbound firewall port";

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

    ingress = lib.mkOption {
      type = lib.types.listOf ingressRouteSubmodule;
      default = [ ];
      description = "Explicit hostname-to-loopback routes published through this tunnel; every undeclared hostname receives a 404.";
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
