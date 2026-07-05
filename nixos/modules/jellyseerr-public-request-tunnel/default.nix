{
  config,
  lib,
  ...
}:
let
  jellyseerrPublicRequestTunnelConfig = config.custom.jellyseerrPublicRequestTunnel;
in
{
  options.custom.jellyseerrPublicRequestTunnel = {
    enable = lib.mkEnableOption "the dedicated Cloudflare Tunnel that publishes only the Jellyseerr request portal to the public internet so approved friends reach it over a friendly hostname while every other arr-stack service stays reachable only across the tailnet";

    tunnelId = lib.mkOption {
      type = lib.types.str;
      default = "";
      description = "Cloudflare Tunnel UUID this connector runs, minted for the media request portal and kept separate from the owner-only Jarvis session tunnel so the public request portal and the owner cockpit never share a credential.";
    };

    credentialsFile = lib.mkOption {
      type = lib.types.str;
      default = "";
      description = "Path to the decrypted Cloudflare Tunnel credentials JSON for the media request portal tunnel, provisioned through agenix so the account tag and tunnel secret never enter the Nix store.";
    };

    publicRequestHostname = lib.mkOption {
      type = lib.types.str;
      default = "requests.lucaszanoni.com";
      description = "Public hostname the Cloudflare edge routes through this tunnel to the Jellyseerr request portal; every other hostname is answered with a 404 so the tunnel exposes nothing beyond the request portal.";
    };

    jellyseerrTailnetServiceUrl = lib.mkOption {
      type = lib.types.str;
      default = "http://100.94.11.81:5055";
      description = "Tailnet-bound URL of the co-located Jellyseerr container the tunnel forwards the public request hostname to; Jellyseerr keeps binding the tailscale address only so this tunnel stays the single public entry point.";
    };
  };

  config = lib.mkIf jellyseerrPublicRequestTunnelConfig.enable {
    services.cloudflared = {
      enable = true;
      tunnels.${jellyseerrPublicRequestTunnelConfig.tunnelId} = {
        inherit (jellyseerrPublicRequestTunnelConfig) credentialsFile;
        default = "http_status:404";
        ingress = {
          ${jellyseerrPublicRequestTunnelConfig.publicRequestHostname} =
            jellyseerrPublicRequestTunnelConfig.jellyseerrTailnetServiceUrl;
        };
      };
    };
  };
}
