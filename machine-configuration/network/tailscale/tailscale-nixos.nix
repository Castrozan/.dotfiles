{ config, pkgs, ... }:
{
  assertions = [
    {
      assertion = config.networking.firewall.checkReversePath == "loose";
      message = "Loose reverse path filtering is required — Tailscale uses WireGuard which sends packets from source addresses that differ from the interface address; strict rp_filter drops these packets silently breaking all Tailscale connectivity";
    }
    {
      assertion = builtins.elem "tailscale0" config.networking.firewall.trustedInterfaces;
      message = "tailscale0 must be a trusted firewall interface — without this, the firewall blocks inter-node traffic on the Tailscale mesh even though Tailscale itself authenticated and encrypted it";
    }
  ];

  services.tailscale.enable = true;

  systemd.services.tailnet-route-in-main-table = {
    description = "Keep the tailnet reachable while a full-tunnel VPN holds the default route — wg-quick installs its rules just above the tailscale rule owning the tailnet table, so 100.64.0.0/10 otherwise vanishes into the VPN tunnel; wg-quick consults the main table first for anything more specific than a default route, so this route survives the capture";
    after = [ "tailscaled.service" ];
    wantedBy = [ "tailscaled.service" ];
    serviceConfig = {
      Type = "oneshot";
      RemainAfterExit = true;
      Restart = "on-failure";
      RestartSec = 2;
      ExecStart = "${pkgs.iproute2}/bin/ip route replace 100.64.0.0/10 dev tailscale0";
    };
  };

  networking.firewall = {
    trustedInterfaces = [
      "tailscale0"
      "wgnord"
    ];
    checkReversePath = "loose";
  };
}
