{ config, ... }:
{
  assertions = [
    {
      assertion = config.networking.resolvconf.enable;
      message = "openresolv must own /etc/resolv.conf — wgnord and tailscaled each claim it exclusively through resolvconf, openresolv hands the whole file to whichever claimed it last, and tailscaled re-claims it on the link-change event that bringing the NordVPN tunnel up fires, so without an ordering policy the Nord nameservers never reach resolv.conf and every hostname lookup dies the moment the tunnel takes the default route";
    }
  ];

  networking.resolvconf.extraConfig = ''
    inclusive_interfaces="tailscale wgnord"
    interface_order="lo lo[0-9]* wgnord tailscale"
  '';
}
