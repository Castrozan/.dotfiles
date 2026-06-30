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

  chromeDarwinPolicyConfig = import ../default.nix;
  chromeDarwinManagedPolicyKeys =
    chromeDarwinPolicyConfig.system.defaults.CustomUserPreferences."com.google.Chrome";

  memorySaverIsForcedOnByPolicy = chromeDarwinManagedPolicyKeys.HighEfficiencyModeEnabled;
  memorySaverSavingsLevelIsBalancedByPolicy =
    chromeDarwinManagedPolicyKeys.MemorySaverModeSavings == 1;

  keystoneAutoUpdateDisabledByPolicy =
    chromeDarwinPolicyConfig.system.defaults.CustomUserPreferences."com.google.Keystone.Agent".checkInterval
    == 0;
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
}
