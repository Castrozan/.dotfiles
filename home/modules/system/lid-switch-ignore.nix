{ config, lib, ... }:

let
  dotfilesDir = "${config.home.homeDirectory}/.dotfiles";
in
{
  home.activation.setupLidSwitchIgnore = lib.hm.dag.entryAfter [ "writeBoundary" ] ''
    PATH="/usr/bin:/usr/sbin:/sbin:$PATH"

    if [ -f /etc/NIXOS ]; then
      $VERBOSE_ECHO "Skipping lid switch setup on NixOS (use nixos/modules/lid-switch.nix)"
    elif [ -f /etc/systemd/logind.conf.d/lid-switch.conf ] \
      && grep -q "HandleLidSwitch=ignore" /etc/systemd/logind.conf.d/lid-switch.conf 2>/dev/null \
      && grep -q "HandleLidSwitchExternalPower=ignore" /etc/systemd/logind.conf.d/lid-switch.conf 2>/dev/null \
      && grep -q "HandleLidSwitchDocked=ignore" /etc/systemd/logind.conf.d/lid-switch.conf 2>/dev/null; then
      $VERBOSE_ECHO "Lid switch ignore already configured"
    else
      echo "Setting up lid switch ignore (requires sudo)..."
      sudo "${dotfilesDir}/home/modules/system/scripts/setup-lid-switch-ignore"
    fi
  '';
}
