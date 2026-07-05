{
  config,
  lib,
  pkgs,
  ...
}:
let
  jellyfinTailscaleFunnelConfig = config.custom.jellyfinTailscaleFunnel;
in
{
  options.custom.jellyfinTailscaleFunnel = {
    enable = lib.mkEnableOption "publishing Jellyfin to the public internet over Tailscale Funnel so approved friends reach the media server on its funnel hostname without joining the tailnet, while every other arr-stack service stays reachable only across the tailnet";

    jellyfinLoopbackUrl = lib.mkOption {
      type = lib.types.str;
      default = "http://127.0.0.1:8096";
      description = "Loopback URL of the Jellyfin container the Tailscale Funnel proxies to; Jellyfin publishes this 127.0.0.1 address only for the funnel and keeps its tailnet bind for in-tailnet clients, because Funnel accepts loopback proxy targets only.";
    };
  };

  config = lib.mkIf jellyfinTailscaleFunnelConfig.enable {
    systemd.services.jellyfin-tailscale-funnel = {
      description = "Assert the Tailscale Funnel that publishes Jellyfin to the public internet";
      after = [
        "tailscaled.service"
        "network-online.target"
      ];
      wants = [
        "tailscaled.service"
        "network-online.target"
      ];
      wantedBy = [ "multi-user.target" ];
      serviceConfig = {
        Type = "oneshot";
        RemainAfterExit = true;
        ExecStart = "${pkgs.tailscale}/bin/tailscale funnel --bg ${jellyfinTailscaleFunnelConfig.jellyfinLoopbackUrl}";
      };
    };
  };
}
