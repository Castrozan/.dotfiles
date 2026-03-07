{ config, lib, ... }:

let
  dotfilesDir = "${config.home.homeDirectory}/.dotfiles";
in
{
  home.activation.setupNetworkOptimization = lib.hm.dag.entryAfter [ "writeBoundary" ] ''
    PATH="/usr/bin:/usr/sbin:/sbin:$PATH"

    if [ -f /etc/NIXOS ]; then
      $VERBOSE_ECHO "Skipping network optimization setup on NixOS"
    elif [ "$(sysctl -n net.ipv4.tcp_congestion_control 2>/dev/null)" = "bbr" ] \
      && [ "$(sysctl -n net.core.rmem_max 2>/dev/null)" = "16777216" ] \
      && [ "$(sysctl -n net.core.wmem_max 2>/dev/null)" = "16777216" ] \
      && [ "$(sysctl -n net.ipv4.tcp_fastopen 2>/dev/null)" = "3" ] \
      && [ "$(sysctl -n net.ipv4.tcp_slow_start_after_idle 2>/dev/null)" = "0" ] \
      && [ "$(sysctl -n net.ipv4.tcp_mtu_probing 2>/dev/null)" = "1" ] \
      && [ "$(sysctl -n net.core.netdev_max_backlog 2>/dev/null)" = "16384" ] \
      && grep -q "wifi.powersave = 2" /etc/NetworkManager/conf.d/wifi-powersave-off.conf 2>/dev/null \
      && grep -q "DNSOverTLS=yes" /etc/systemd/resolved.conf.d/dns-optimization.conf 2>/dev/null; then
      $VERBOSE_ECHO "Network optimization already configured"
    else
      echo "Setting up network optimization (requires sudo)..."
      sudo "${dotfilesDir}/bin/setup-network-optimization"
    fi
  '';
}
