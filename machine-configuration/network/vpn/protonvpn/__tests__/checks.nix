{
  helpers,
  lib,
  pkgs,
  self,
  ...
}:
let
  inherit (helpers) mkEvalCheck;

  nixosConfiguration = self.nixosConfigurations.chise.config;
  protonVpnConfiguration = nixosConfiguration.services.openvpn.servers.proton-paraguay;
in
{
  chise-proton-vpn-uses-systemd-resolved =
    mkEvalCheck "chise-proton-vpn-uses-systemd-resolved"
      (
        nixosConfiguration.services.resolved.enable
        && nixosConfiguration.networking.networkmanager.dns == "systemd-resolved"
      )
      "Proton VPN and Tailscale must publish per-link DNS through systemd-resolved instead of competing for resolv.conf";

  chise-proton-vpn-registers-proton-dns-as-default-route =
    mkEvalCheck "chise-proton-vpn-registers-proton-dns-as-default-route"
      (lib.hasInfix "dhcp-option DOMAIN-ROUTE ." protonVpnConfiguration.config)
      "the Proton tunnel must own the systemd-resolved root routing domain so public DNS cannot leak to the physical link";

  chise-proton-vpn-uses-resolved-adapter =
    mkEvalCheck "chise-proton-vpn-uses-resolved-adapter"
      (
        !protonVpnConfiguration.updateResolvConf
        && lib.hasInfix "update-systemd-resolved" protonVpnConfiguration.up
        && lib.hasInfix "update-systemd-resolved" protonVpnConfiguration.down
      )
      "OpenVPN must register and remove Proton DNS on tun0 through update-systemd-resolved rather than openresolv";

  chise-proton-vpn-accepts-profile-resolver-hook =
    mkEvalCheck "chise-proton-vpn-accepts-profile-resolver-hook"
      (
        nixosConfiguration.environment.etc ? "openvpn/update-resolv-conf"
        &&
          nixosConfiguration.environment.etc."openvpn/update-resolv-conf".source
          == "${pkgs.update-systemd-resolved}/libexec/openvpn/update-systemd-resolved"
      )
      "the resolver hook path embedded in the Proton profile must resolve to the systemd-resolved adapter";

  chise-proton-vpn-resolver-lifecycle-follows-tunnel =
    mkEvalCheck "chise-proton-vpn-resolver-lifecycle-follows-tunnel"
      (
        lib.hasInfix "up-restart" protonVpnConfiguration.config
        && lib.hasInfix "down-pre" protonVpnConfiguration.config
      )
      "OpenVPN must reassert DNS after a persistent-tunnel restart and remove it before tun0 disappears";

  chise-proton-vpn-requires-resolver = mkEvalCheck "chise-proton-vpn-requires-resolver" (
    builtins.elem "systemd-resolved.service" nixosConfiguration.systemd.services.openvpn-proton-paraguay.requires
    && builtins.elem "systemd-resolved.service" nixosConfiguration.systemd.services.openvpn-proton-paraguay.after
  ) "the Proton tunnel must fail closed when systemd-resolved is unavailable";
}
