{ config, lib, ... }:

let
  dotfilesDir = "${config.home.homeDirectory}/.dotfiles";
in
{
  home.activation.setupUbuntuSystemTuning = lib.hm.dag.entryAfter [ "writeBoundary" ] ''
    PATH="/usr/bin:/usr/sbin:/sbin:$PATH"

    if [ -f /etc/NIXOS ]; then
      $VERBOSE_ECHO "Skipping Ubuntu system tuning on NixOS"
    elif [ "$(sysctl -n vm.vfs_cache_pressure 2>/dev/null)" = "50" ] \
      && ! systemctl is-active --quiet ModemManager 2>/dev/null \
      && ! systemctl is-active --quiet avahi-daemon 2>/dev/null \
      && ! systemctl is-active --quiet cups 2>/dev/null \
      && ! command -v snap >/dev/null 2>&1 \
      && [ -f /etc/systemd/journald.conf.d/size-cap.conf ] \
      && grep -q "SystemMaxUse=500M" /etc/systemd/journald.conf.d/size-cap.conf 2>/dev/null; then
      $VERBOSE_ECHO "Ubuntu system tuning already configured"
    else
      echo "Setting up Ubuntu system tuning (requires sudo)..."
      sudo "${dotfilesDir}/home/modules/system/scripts/setup-ubuntu-system-tuning"
    fi
  '';
}
