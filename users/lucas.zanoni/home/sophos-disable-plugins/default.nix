{ config, lib, ... }:
let
  dotfilesDir = "${config.home.homeDirectory}/.dotfiles";
  installerScriptPath = "${dotfilesDir}/users/lucas.zanoni/home/sophos-disable-plugins/install-systemd-service";
  stopScriptSourcePath = "${dotfilesDir}/users/lucas.zanoni/home/sophos-disable-plugins/stop-sophos-noisy-plugins";
  installedSystemdUnitPath = "/etc/systemd/system/sophos-disable-noisy-plugins.service";
  installedStopScriptPath = "/usr/local/sbin/sophos-disable-noisy-plugins-stop";
in
{
  home.activation.setupSophosDisableNoisyPlugins = lib.hm.dag.entryAfter [ "writeBoundary" ] ''
    PATH="/usr/bin:/usr/sbin:/sbin:$PATH"

    if [ ! -x /opt/sophos-spl/bin/wdctl ]; then
      $VERBOSE_ECHO "sophos-spl not installed, skipping noisy plugin disabler"
    elif [ -f "${installedSystemdUnitPath}" ] \
      && [ -x "${installedStopScriptPath}" ] \
      && cmp -s "${stopScriptSourcePath}" "${installedStopScriptPath}" \
      && systemctl is-enabled --quiet sophos-disable-noisy-plugins.service 2>/dev/null; then
      $VERBOSE_ECHO "sophos-disable-noisy-plugins.service already installed and matches source"
    else
      echo "Installing sophos-disable-noisy-plugins.service (requires sudo)..."
      sudo "${installerScriptPath}"
    fi
  '';
}
