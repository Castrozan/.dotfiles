{
  pkgs,
  lib,
  ...
}:
let
  helpers = import ../../../../tests/nix-checks/helpers.nix {
    inherit pkgs lib;
    inputs = null;
    nixpkgs-version = null;
    home-version = null;
  };
  inherit (helpers) mkEvalCheck;

  chromeDarwinPolicyConfig = import ../default.nix { inherit lib; };
  chromeDarwinManagedPolicyKeys =
    chromeDarwinPolicyConfig.system.defaults.CustomUserPreferences."com.google.Chrome";

  memorySaverIsForcedOnByPolicy = chromeDarwinManagedPolicyKeys.HighEfficiencyModeEnabled;
  memorySaverSavingsLevelIsBalancedByPolicy =
    chromeDarwinManagedPolicyKeys.MemorySaverModeSavings == 1;

  keystoneAutoUpdateDisabledByPolicy =
    chromeDarwinPolicyConfig.system.defaults.CustomUserPreferences."com.google.Keystone.Agent".checkInterval
    == 0;

  keystoneManagedPreferenceInstallScript =
    chromeDarwinPolicyConfig.system.activationScripts.postActivation.text.content;
  keystoneUpdatesForcedDisabledByManagedPreference =
    lib.hasInfix "/Library/Managed Preferences/com.google.Keystone.plist" keystoneManagedPreferenceInstallScript
    && lib.hasInfix "<key>UpdateDefault</key>" keystoneManagedPreferenceInstallScript
    && lib.hasInfix "<integer>3</integer>" keystoneManagedPreferenceInstallScript;
in
{
  macbook-chrome-memory-saver-forced-on =
    mkEvalCheck "macbook-chrome-memory-saver-forced-on" memorySaverIsForcedOnByPolicy
      "Chrome HighEfficiencyModeEnabled must be true so inactive tabs are discarded to reclaim memory";

  macbook-chrome-memory-saver-savings-balanced =
    mkEvalCheck "macbook-chrome-memory-saver-savings-balanced" memorySaverSavingsLevelIsBalancedByPolicy
      "Chrome MemorySaverModeSavings must equal 1 (balanced) to discard inactive tabs without excessive reloads";

  macbook-chrome-keystone-auto-update-disabled =
    mkEvalCheck "macbook-chrome-keystone-auto-update-disabled" keystoneAutoUpdateDisabledByPolicy
      "Chrome Keystone checkInterval must be 0 so the updater never swaps the on-disk install underneath the long-lived chrome-global browser, the version desync that wedges chrome-devtools-mcp autoConnect";

  macbook-chrome-keystone-updates-forced-disabled =
    mkEvalCheck "macbook-chrome-keystone-updates-forced-disabled"
      keystoneUpdatesForcedDisabledByManagedPreference
      "Chrome must install a forced managed preference /Library/Managed Preferences/com.google.Keystone.plist with updatePolicies.global.UpdateDefault=3, the only authoritative full-stop the root Keystone/GoogleUpdater daemon honors; value 3 is Disabled on the Managed Preferences integer scale (0 Enabled, 1 Automatic only, 2 Manual only, 3 Disabled), and a plain per-user default cannot deliver it";
}
