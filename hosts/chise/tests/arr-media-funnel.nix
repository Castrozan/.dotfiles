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

  evalArrMediaTailscaleFunnel =
    funnelSettings:
    (lib.evalModules {
      modules = [
        ../../../nixos/modules/arr-media-tailscale-funnel
        {
          options.systemd.services = lib.mkOption {
            type = lib.types.attrs;
            default = { };
          };
          config.custom.arrMediaTailscaleFunnel = funnelSettings;
          config._module.args.pkgs = pkgs;
        }
      ];
    }).config;

  arrMediaTailscaleFunnelDisabled = evalArrMediaTailscaleFunnel {
    enable = false;
  };

  arrMediaTailscaleFunnelEnabled = evalArrMediaTailscaleFunnel {
    enable = true;
    funnels = [
      {
        publicHttpsPort = 443;
        loopbackUrl = "http://127.0.0.1:8096";
      }
      {
        publicHttpsPort = 8443;
        loopbackUrl = "http://127.0.0.1:5055";
      }
    ];
  };

  arrMediaTailscaleFunnelUnit =
    arrMediaTailscaleFunnelEnabled.systemd.services.arr-media-tailscale-funnel;

  execStartCommands = lib.concatStringsSep "\n" arrMediaTailscaleFunnelUnit.serviceConfig.ExecStart;
in
{
  chise-arr-media-tailscale-funnel-disabled-publishes-nothing =
    mkEvalCheck "chise-arr-media-tailscale-funnel-disabled-publishes-nothing"
      (!(arrMediaTailscaleFunnelDisabled.systemd.services ? arr-media-tailscale-funnel))
      "the arr-stack media funnel must assert no funnel service while disabled, so a host that does not opt in exposes the media services only across the tailnet";

  chise-arr-media-tailscale-funnel-enabled-defines-oneshot =
    mkEvalCheck "chise-arr-media-tailscale-funnel-enabled-defines-oneshot"
      (arrMediaTailscaleFunnelUnit.serviceConfig.Type == "oneshot")
      "an enabled arr-stack media funnel must assert the funnels through a oneshot unit that re-applies the persistent serve config on boot";

  chise-arr-media-tailscale-funnel-publishes-jellyfin-loopback =
    mkEvalCheck "chise-arr-media-tailscale-funnel-publishes-jellyfin-loopback"
      (lib.hasInfix "tailscale funnel --https=443 --bg http://127.0.0.1:8096" execStartCommands)
      "the funnel unit must publish the Jellyfin loopback on 443, since Tailscale Funnel accepts only loopback proxy targets and Jellyfin exposes 127.0.0.1:8096 for exactly this";

  chise-arr-media-tailscale-funnel-publishes-jellyseerr-loopback =
    mkEvalCheck "chise-arr-media-tailscale-funnel-publishes-jellyseerr-loopback"
      (lib.hasInfix "tailscale funnel --https=8443 --bg http://127.0.0.1:5055" execStartCommands)
      "the funnel unit must publish the Jellyseerr loopback on the distinct 8443 funnel port so friends reach the request portal without colliding with the Jellyfin funnel on 443";

  chise-arr-media-tailscale-funnel-enabled-wanted-by-multi-user =
    mkEvalCheck "chise-arr-media-tailscale-funnel-enabled-wanted-by-multi-user"
      (builtins.elem "multi-user.target" arrMediaTailscaleFunnelUnit.wantedBy)
      "the funnel unit must be wanted by multi-user.target so the public media exposure is re-asserted on every boot";

  chise-arr-media-tailscale-funnel-enabled-after-tailscaled =
    mkEvalCheck "chise-arr-media-tailscale-funnel-enabled-after-tailscaled"
      (builtins.elem "tailscaled.service" arrMediaTailscaleFunnelUnit.after)
      "the funnel unit must order after tailscaled so the serve config is applied against a running Tailscale daemon";

  chise-arr-media-tailscale-funnel-waits-for-tailscale-backend-running =
    mkEvalCheck "chise-arr-media-tailscale-funnel-waits-for-tailscale-backend-running"
      (lib.hasInfix "wait-for-tailscale-backend-running" arrMediaTailscaleFunnelUnit.serviceConfig.ExecStartPre)
      "the funnel unit must wait for the Tailscale backend to reach Running before asserting the serve config, because ordering after tailscaled only waits for the daemon to start, not to authenticate, so on a cold boot the oneshot otherwise runs against a NoState backend, exits 1 and drops the public media exposure until a manual restart";
}
