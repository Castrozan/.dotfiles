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

  evalJellyfinTailscaleFunnel =
    funnelSettings:
    (lib.evalModules {
      modules = [
        ../../../nixos/modules/jellyfin-tailscale-funnel
        {
          options.systemd.services = lib.mkOption {
            type = lib.types.attrs;
            default = { };
          };
          config.custom.jellyfinTailscaleFunnel = funnelSettings;
          config._module.args.pkgs = pkgs;
        }
      ];
    }).config;

  jellyfinTailscaleFunnelDisabled = evalJellyfinTailscaleFunnel {
    enable = false;
  };

  jellyfinTailscaleFunnelEnabled = evalJellyfinTailscaleFunnel {
    enable = true;
  };

  jellyfinTailscaleFunnelUnit =
    jellyfinTailscaleFunnelEnabled.systemd.services.jellyfin-tailscale-funnel;
in
{
  chise-jellyfin-tailscale-funnel-disabled-publishes-nothing =
    mkEvalCheck "chise-jellyfin-tailscale-funnel-disabled-publishes-nothing"
      (!(jellyfinTailscaleFunnelDisabled.systemd.services ? jellyfin-tailscale-funnel))
      "the Jellyfin Tailscale Funnel must assert no funnel service while disabled, so a host that does not opt in exposes Jellyfin only across the tailnet";

  chise-jellyfin-tailscale-funnel-enabled-defines-oneshot =
    mkEvalCheck "chise-jellyfin-tailscale-funnel-enabled-defines-oneshot"
      (jellyfinTailscaleFunnelUnit.serviceConfig.Type == "oneshot")
      "an enabled Jellyfin Tailscale Funnel must assert the funnel through a oneshot unit that re-applies the persistent serve config on boot";

  chise-jellyfin-tailscale-funnel-enabled-runs-tailscale-funnel-to-loopback =
    mkEvalCheck "chise-jellyfin-tailscale-funnel-enabled-runs-tailscale-funnel-to-loopback"
      (lib.hasInfix "tailscale funnel --bg http://127.0.0.1:8096" jellyfinTailscaleFunnelUnit.serviceConfig.ExecStart)
      "the funnel unit must publish the Jellyfin loopback address to the public internet, since Tailscale Funnel accepts only loopback proxy targets and Jellyfin exposes 127.0.0.1:8096 for exactly this";

  chise-jellyfin-tailscale-funnel-enabled-wanted-by-multi-user =
    mkEvalCheck "chise-jellyfin-tailscale-funnel-enabled-wanted-by-multi-user"
      (builtins.elem "multi-user.target" jellyfinTailscaleFunnelUnit.wantedBy)
      "the funnel unit must be wanted by multi-user.target so the public Jellyfin exposure is re-asserted on every boot";

  chise-jellyfin-tailscale-funnel-enabled-after-tailscaled =
    mkEvalCheck "chise-jellyfin-tailscale-funnel-enabled-after-tailscaled"
      (builtins.elem "tailscaled.service" jellyfinTailscaleFunnelUnit.after)
      "the funnel unit must order after tailscaled so the serve config is applied against a running Tailscale daemon";
}
