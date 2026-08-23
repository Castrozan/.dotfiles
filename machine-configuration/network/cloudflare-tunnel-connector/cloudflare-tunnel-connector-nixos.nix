{
  config,
  lib,
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
      description = "Path to the decrypted Cloudflare Tunnel connector credentials JSON, provisioned through agenix so the account tag and tunnel secret never land in the Nix store.";
    };

    ingress = lib.mkOption {
      type = lib.types.listOf ingressRouteSubmodule;
      default = [ ];
      description = "Explicit hostname-to-loopback routes published through this tunnel; every undeclared hostname receives a 404.";
    };
  };

  config = lib.mkIf cloudflareTunnelConnectorConfig.enable {
    services.cloudflared = {
      enable = true;
      tunnels.${cloudflareTunnelConnectorConfig.tunnelId} = {
        inherit (cloudflareTunnelConnectorConfig) credentialsFile;
        default = "http_status:404";
        ingress = builtins.listToAttrs (
          map (route: {
            name = route.hostname;
            value = route.localServiceUrl;
          }) cloudflareTunnelConnectorConfig.ingress
        );
      };
    };
  };
}
