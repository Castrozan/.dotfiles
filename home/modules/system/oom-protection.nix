{ config, lib, ... }:

let
  dotfilesDir = "${config.home.homeDirectory}/.dotfiles";
in
{
  home.activation.setupOomProtection = lib.hm.dag.entryAfter [ "writeBoundary" ] ''
    PATH="/usr/bin:/usr/sbin:/sbin:$PATH"

    if [ -f /etc/NIXOS ]; then
      $VERBOSE_ECHO "Skipping OOM protection setup on NixOS"
    elif command -v earlyoom >/dev/null 2>&1 \
      && grep -q "ALGO=zstd" /etc/default/zramswap 2>/dev/null \
      && grep -q "PERCENT=50" /etc/default/zramswap 2>/dev/null \
      && grep -q "\-m 10" /etc/default/earlyoom 2>/dev/null \
      && [ "$(sysctl -n vm.swappiness 2>/dev/null)" = "150" ]; then
      $VERBOSE_ECHO "OOM protection already configured"
    else
      echo "Setting up OOM protection (requires sudo)..."
      sudo "${dotfilesDir}/bin/setup-oom-protection"
    fi
  '';
}
