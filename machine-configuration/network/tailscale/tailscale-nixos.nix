{ config, ... }:
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

  networking.firewall = {
    trustedInterfaces = [
      "tailscale0"
      "wgnord"
    ];
    checkReversePath = "loose";
  };
}
