{ config, ... }:
{
  assertions = [
    {
      assertion = config.networking.resolvconf.enable;
      message = "openresolv must own /etc/resolv.conf — wgnord and tailscaled each claim it exclusively, openresolv hands the whole file to whichever claimed it last, and bringing the NordVPN tunnel up fires the link-change event that makes tailscaled re-claim, so without an ordering policy the file holds exactly one resolver and nothing can back it up";
    }
  ];

  networking.resolvconf.extraConfig = ''
    inclusive_interfaces="tailscale wgnord"
    interface_order="lo lo[0-9]* tailscale wgnord"
  '';
}
