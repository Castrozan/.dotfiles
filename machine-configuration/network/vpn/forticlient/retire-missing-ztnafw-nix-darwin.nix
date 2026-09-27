{ lib, ... }:
{
  system.activationScripts.postActivation.text = lib.mkAfter ''
    forticlientZtnaExecutable="/Library/Application Support/Fortinet/FortiClient/bin/ztnafw"
    forticlientZtnaDaemon="/Library/LaunchDaemons/com.fortinet.forticlient.ztnafw.plist"
    if [ ! -e "$forticlientZtnaExecutable" ] && [ -f "$forticlientZtnaDaemon" ]; then
      if /bin/launchctl print system/com.fortinet.ztnafw >/dev/null 2>&1; then
        /bin/launchctl bootout system/com.fortinet.ztnafw || exit 1
      fi
      /bin/rm -- "$forticlientZtnaDaemon"
    fi
  '';
}
