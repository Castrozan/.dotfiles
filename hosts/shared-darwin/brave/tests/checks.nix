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

  braveDarwinPolicyConfig = import ../default.nix { inherit lib; };
  braveDarwinManagedPolicyKeys =
    braveDarwinPolicyConfig.system.defaults.CustomUserPreferences."com.brave.Browser";

  bookmarkBarIsForcedOnByPolicy = braveDarwinManagedPolicyKeys.BookmarkBarEnabled;
  googleSigninIsDisabledByPolicy = braveDarwinManagedPolicyKeys.BrowserSignin == 0;
  spellcheckRemoteServiceIsDisabledByPolicy = !braveDarwinManagedPolicyKeys.SpellCheckServiceEnabled;
  spellcheckLanguageIsLockedToEnGbByPolicy =
    braveDarwinManagedPolicyKeys.SpellcheckLanguage == [ "en-GB" ];
  allPrivacySandboxApisAreDisabledByPolicy =
    !braveDarwinManagedPolicyKeys.PrivacySandboxAdTopicsEnabled
    && !braveDarwinManagedPolicyKeys.PrivacySandboxSiteEnabledAdsEnabled
    && !braveDarwinManagedPolicyKeys.PrivacySandboxAdMeasurementEnabled;
  telemetryAndStatsPingsAreDisabledByPolicy =
    !braveDarwinManagedPolicyKeys.MetricsReportingEnabled
    && !braveDarwinManagedPolicyKeys.BraveStatsPingEnabled
    && !braveDarwinManagedPolicyKeys.BraveP3AEnabled;
  sparkleAutoUpdateIsDisabledByPolicy =
    !braveDarwinManagedPolicyKeys.SUEnableAutomaticChecks
    && !braveDarwinManagedPolicyKeys.SUAutomaticallyUpdate;

  braveUpdaterManagedPreferenceInstallScript =
    braveDarwinPolicyConfig.system.activationScripts.postActivation.text.content;
  braveUpdaterUpdatesForcedDisabledByManagedPreference =
    lib.hasInfix "/Library/Managed Preferences/com.brave.Keystone.plist" braveUpdaterManagedPreferenceInstallScript
    && lib.hasInfix "<key>UpdateDefault</key>" braveUpdaterManagedPreferenceInstallScript
    && lib.hasInfix "<integer>3</integer>" braveUpdaterManagedPreferenceInstallScript;
in
{
  macbook-brave-bookmark-bar-forced-on =
    mkEvalCheck "macbook-brave-bookmark-bar-forced-on" bookmarkBarIsForcedOnByPolicy
      "Brave BookmarkBarEnabled must be true in CustomUserPreferences";

  macbook-brave-google-signin-disabled =
    mkEvalCheck "macbook-brave-google-signin-disabled" googleSigninIsDisabledByPolicy
      "Brave BrowserSignin must equal 0 (disabled) in CustomUserPreferences";

  macbook-brave-spellcheck-remote-service-disabled =
    mkEvalCheck "macbook-brave-spellcheck-remote-service-disabled"
      spellcheckRemoteServiceIsDisabledByPolicy
      "Brave SpellCheckServiceEnabled must be false to keep dictionary checking local";

  macbook-brave-spellcheck-language-locked-to-en-gb =
    mkEvalCheck "macbook-brave-spellcheck-language-locked-to-en-gb"
      spellcheckLanguageIsLockedToEnGbByPolicy
      "Brave SpellcheckLanguage must contain exactly en-GB";

  macbook-brave-privacy-sandbox-apis-disabled =
    mkEvalCheck "macbook-brave-privacy-sandbox-apis-disabled" allPrivacySandboxApisAreDisabledByPolicy
      "Brave Privacy Sandbox APIs (Topics, Fledge, AdMeasurement) must all be disabled";

  macbook-brave-telemetry-disabled =
    mkEvalCheck "macbook-brave-telemetry-disabled" telemetryAndStatsPingsAreDisabledByPolicy
      "Brave MetricsReporting, BraveStatsPing, and BraveP3A must all be disabled";

  macbook-brave-sparkle-auto-update-disabled =
    mkEvalCheck "macbook-brave-sparkle-auto-update-disabled" sparkleAutoUpdateIsDisabledByPolicy
      "Brave Sparkle SUEnableAutomaticChecks and SUAutomaticallyUpdate must be false so the updater never swaps the install underneath a running Brave, mirroring the Chrome Keystone disable";

  macbook-brave-updater-updates-forced-disabled =
    mkEvalCheck "macbook-brave-updater-updates-forced-disabled"
      braveUpdaterUpdatesForcedDisabledByManagedPreference
      "Brave must install a forced managed preference /Library/Managed Preferences/com.brave.Keystone.plist with updatePolicies.global.UpdateDefault=3 so the bundled Chromium/Omaha BraveUpdater stays disabled when Brave promotes it away from Sparkle; the SU* keys do not govern that updater, and value 3 is Disabled on the Managed Preferences integer scale (not 0, which is Enabled there)";
}
