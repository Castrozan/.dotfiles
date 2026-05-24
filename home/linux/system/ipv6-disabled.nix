{ config, lib, ... }:

let
  dotfilesDir = "${config.home.homeDirectory}/.dotfiles";
in
{
  home.activation.setupIpv6Disabled = lib.hm.dag.entryAfter [ "writeBoundary" ] ''
    PATH="/usr/bin:/usr/sbin:/sbin:$PATH"

    if [ -f /etc/NIXOS ]; then
      $VERBOSE_ECHO "Skipping IPv6 disable on NixOS"
    elif nmcli connection show "Zanoni" 2>/dev/null | grep -q "ipv6.method:.*disabled"; then
      $VERBOSE_ECHO "IPv6 already disabled on Zanoni"
    else
      echo "Disabling IPv6 on Zanoni connection..."
      "${dotfilesDir}/home/modules/system/scripts/setup-ipv6-disabled"
    fi
  '';
}
