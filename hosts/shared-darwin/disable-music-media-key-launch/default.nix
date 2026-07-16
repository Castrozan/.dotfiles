{
  lib,
  username,
  ...
}:
{
  system.activationScripts.postActivation.text = lib.mkAfter ''
    echo "disabling com.apple.rcd so the play media key stops launching Music.app..." >&2
    musicMediaKeyDaemonOwnerUserId=$(/usr/bin/id -u ${lib.escapeShellArg username})
    /bin/launchctl disable "gui/$musicMediaKeyDaemonOwnerUserId/com.apple.rcd" || true
    /bin/launchctl bootout "gui/$musicMediaKeyDaemonOwnerUserId/com.apple.rcd" 2>/dev/null || true
  '';
}
