{
  pkgs,
  lib,
  ...
}:
let
  helpers = import ../../../../__tests__/nix-checks/helpers.nix {
    inherit pkgs lib;
    inputs = null;
    nixpkgs-version = null;
    home-version = null;
  };
  inherit (helpers) mkEvalCheck;

  chromeDarwinPolicyConfig = import ../default.nix {
    inherit lib;
    username = "chrome-policy-check-user";
  };

  keystoneAutoUpdateDisabledByPolicy =
    chromeDarwinPolicyConfig.system.defaults.CustomUserPreferences."com.google.Keystone.Agent".checkInterval
    == 0;

  keystoneManagedPreferenceInstallScript =
    chromeDarwinPolicyConfig.system.activationScripts.postActivation.text.content;
  keystoneUpdatesForcedDisabledByManagedPreference =
    lib.hasInfix "/Library/Managed Preferences/com.google.Keystone.plist" keystoneManagedPreferenceInstallScript
    && lib.hasInfix "<key>UpdateDefault</key>" keystoneManagedPreferenceInstallScript
    && lib.hasInfix "<integer>3</integer>" keystoneManagedPreferenceInstallScript;

  removeGoogleUpdaterAndBlockReinstallScriptSource = builtins.readFile ../scripts/remove-google-updater-and-block-reinstall.sh;

  googleUpdaterRemovedByActivation =
    lib.hasInfix "remove-google-updater-and-block-reinstall.sh" keystoneManagedPreferenceInstallScript
    && lib.hasInfix "com.google.GoogleUpdater.wake.system" removeGoogleUpdaterAndBlockReinstallScriptSource
    && lib.hasInfix "com.google.keystone.daemon" removeGoogleUpdaterAndBlockReinstallScriptSource
    && lib.hasInfix "/bin/launchctl bootout" removeGoogleUpdaterAndBlockReinstallScriptSource;

  googleUpdaterReinstallBlockedInBothScopes =
    lib.hasInfix "/usr/bin/chflags uchg" removeGoogleUpdaterAndBlockReinstallScriptSource
    && lib.hasInfix ''blockUpdaterInstallPath "/Library/Application Support/Google/GoogleUpdater"'' removeGoogleUpdaterAndBlockReinstallScriptSource
    && lib.hasInfix ''blockUpdaterInstallPath "/Library/Google/GoogleSoftwareUpdate"'' removeGoogleUpdaterAndBlockReinstallScriptSource
    && lib.hasInfix ''"$updaterOwnerHomeDirectory/Library/Application Support/Google/GoogleUpdater"'' removeGoogleUpdaterAndBlockReinstallScriptSource
    && lib.hasInfix ''"$updaterOwnerHomeDirectory/Library/Google/GoogleSoftwareUpdate"'' removeGoogleUpdaterAndBlockReinstallScriptSource;
in
{
  macbook-chrome-keystone-auto-update-disabled =
    mkEvalCheck "macbook-chrome-keystone-auto-update-disabled" keystoneAutoUpdateDisabledByPolicy
      "Chrome Keystone checkInterval must be 0 so the legacy per-user Keystone agent never polls for a new version; it throttles only that agent, so it is defence in depth behind the updater removal, never the load-bearing stop";

  macbook-chrome-keystone-updates-forced-disabled =
    mkEvalCheck "macbook-chrome-keystone-updates-forced-disabled"
      keystoneUpdatesForcedDisabledByManagedPreference
      "Chrome must install a forced managed preference /Library/Managed Preferences/com.google.Keystone.plist with updatePolicies.global.UpdateDefault=3, the policy channel the root Keystone/GoogleUpdater daemon reads; value 3 is Disabled on the Managed Preferences integer scale (0 Enabled, 1 Automatic only, 2 Manual only, 3 Disabled), and a plain per-user default cannot deliver it";

  macbook-chrome-google-updater-removed =
    mkEvalCheck "macbook-chrome-google-updater-removed" googleUpdaterRemovedByActivation
      "The activation must boot out and delete the GoogleUpdater/Keystone launchd jobs, because the managed preference above is INERT on this machine: chrome/updater/policy/mac/managed_preference_policy_manager.mm gates HasActiveDevicePolicies on base::IsManagedOrEnterpriseDevice(), so an un-enrolled Mac (profiles status -type enrollment reporting no MDM and no directory binding) silently discards updatePolicies and updates anyway";

  macbook-chrome-google-updater-reinstall-blocked =
    mkEvalCheck "macbook-chrome-google-updater-reinstall-blocked"
      googleUpdaterReinstallBlockedInBothScopes
      "Deleting the updater is not enough because Chrome reinstalls it from its bundled GoogleUpdater.app on every launch, so each install root must be replaced by a root-owned uchg-immutable file that the install cannot overwrite; both the system scope (/Library) and the user scope (~/Library) need it, or Chrome just falls back to the other one";
}
