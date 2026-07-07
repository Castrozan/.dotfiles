{ lib, ... }:
let
  keystoneUpdatesDisabledManagedPreferencePlist = lib.generators.toPlist { escape = true; } {
    updatePolicies = {
      global = {
        UpdateDefault = 3;
      };
    };
  };
in
{
  system.activationScripts.postActivation.text = lib.mkAfter ''
    /bin/mkdir -p "/Library/Managed Preferences"
    printf '%s' ${lib.escapeShellArg keystoneUpdatesDisabledManagedPreferencePlist} > "/Library/Managed Preferences/com.google.Keystone.plist"
    /bin/chmod 0644 "/Library/Managed Preferences/com.google.Keystone.plist"
  '';

  system.defaults.CustomUserPreferences = {
    "com.google.Chrome" = {
      HighEfficiencyModeEnabled = true;
      MemorySaverModeSavings = 1;
    };
    "com.google.Keystone.Agent".checkInterval = 0;
  };
}
