{ ... }:
{
  services.tailscale.enable = true;

  networking.firewall = {
    # Trust Tailscale and WireGuard interfaces (wgnord uses WireGuard)
    trustedInterfaces = [ "tailscale0" "wg0" ];
    checkReversePath = "loose";
  };
}
