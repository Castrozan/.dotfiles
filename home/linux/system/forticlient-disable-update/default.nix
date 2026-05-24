{ config, lib, ... }:
let
  dotfilesDir = "${config.home.homeDirectory}/.dotfiles";
  installerScriptPath = "${dotfilesDir}/home/linux/system/forticlient-disable-update/install-systemd-service";
  disableScriptSourcePath = "${dotfilesDir}/home/linux/system/forticlient-disable-update/disable-forticlient-update";
  installedSystemdUnitPath = "/etc/systemd/system/forticlient-disable-update.service";
  installedDisableScriptPath = "/usr/local/sbin/forticlient-disable-update";
in
{
  home.activation.setupForticlientDisableUpdate = lib.hm.dag.entryAfter [ "writeBoundary" ] ''
    PATH="/usr/bin:/usr/sbin:/sbin:$PATH"

    if ! systemctl list-unit-files forticlient.service --no-legend 2>/dev/null | grep -q forticlient; then
      $VERBOSE_ECHO "forticlient.service not present, skipping update neutralizer"
    elif [ -f "${installedSystemdUnitPath}" ] \
      && [ -x "${installedDisableScriptPath}" ] \
      && cmp -s "${disableScriptSourcePath}" "${installedDisableScriptPath}" \
      && systemctl is-enabled --quiet forticlient-disable-update.service 2>/dev/null; then
      $VERBOSE_ECHO "forticlient-disable-update.service already installed and matches source"
    else
      echo "Installing forticlient-disable-update.service (requires sudo)..."
      sudo "${installerScriptPath}"
    fi
  '';
}
