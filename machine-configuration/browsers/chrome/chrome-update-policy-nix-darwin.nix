{
  lib,
  username,
  ...
}:
let
  keystoneUpdatesDisabledManagedPreferencePlist = lib.generators.toPlist { escape = true; } {
    updatePolicies = {
      global = {
        UpdateDefault = 3;
      };
    };
  };

  removeGoogleUpdaterAndBlockReinstallScript = ./scripts/remove-google-updater-and-block-reinstall.sh;
in
{
  system.activationScripts.postActivation.text = lib.mkAfter ''
    /bin/mkdir -p "/Library/Managed Preferences"
    printf '%s' ${lib.escapeShellArg keystoneUpdatesDisabledManagedPreferencePlist} > "/Library/Managed Preferences/com.google.Keystone.plist"
    /bin/chmod 0644 "/Library/Managed Preferences/com.google.Keystone.plist"
    /bin/bash ${removeGoogleUpdaterAndBlockReinstallScript} ${lib.escapeShellArg username}
  '';

  system.defaults.CustomUserPreferences = {
    "com.google.Keystone.Agent".checkInterval = 0;
  };
}
