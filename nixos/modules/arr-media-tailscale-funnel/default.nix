{
  config,
  lib,
  pkgs,
  ...
}:
let
  arrMediaTailscaleFunnelConfig = config.custom.arrMediaTailscaleFunnel;

  funnelSubmodule = lib.types.submodule {
    options = {
      publicHttpsPort = lib.mkOption {
        type = lib.types.port;
        description = "Public HTTPS port on the funnel hostname this service answers on; Tailscale Funnel only exposes 443, 8443 and 10000, so give each published arr-stack service one of those distinct ports.";
      };

      loopbackUrl = lib.mkOption {
        type = lib.types.str;
        description = "Loopback URL of the container the Tailscale Funnel proxies to; the service publishes this 127.0.0.1 address only for the funnel and keeps its tailnet bind for in-tailnet clients, because Funnel accepts loopback proxy targets only.";
      };
    };
  };
in
{
  options.custom.arrMediaTailscaleFunnel = {
    enable = lib.mkEnableOption "publishing selected arr-stack media services to the public internet over Tailscale Funnel so approved friends reach them on the funnel hostname without joining the tailnet, while every other arr-stack service stays reachable only across the tailnet";

    funnels = lib.mkOption {
      type = lib.types.listOf funnelSubmodule;
      default = [ ];
      description = "The arr-stack services published over Tailscale Funnel, each pinning a distinct public HTTPS port to a loopback proxy target.";
    };
  };

  config = lib.mkIf arrMediaTailscaleFunnelConfig.enable {
    systemd.services.arr-media-tailscale-funnel = {
      description = "Assert the Tailscale Funnels that publish the arr-stack media services to the public internet";
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
        ExecStart = map (
          funnel:
          "${pkgs.tailscale}/bin/tailscale funnel --https=${toString funnel.publicHttpsPort} --bg ${funnel.loopbackUrl}"
        ) arrMediaTailscaleFunnelConfig.funnels;
      };
    };
  };
}
