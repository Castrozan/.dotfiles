_:
{
  services.tailscale.enable = true;

  networking.firewall = {
    # Trust Tailscale and WireGuard interfaces (wgnord uses WireGuard)
    # wgnord creates an interface named "wgnord", not "wg0"
    trustedInterfaces = [ "tailscale0" "wgnord" ];
    checkReversePath = "loose";
  };
}
