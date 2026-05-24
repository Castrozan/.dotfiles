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

  braveDarwinPolicyConfig = import ../default.nix;
  braveDarwinManagedPolicyKeys =
    braveDarwinPolicyConfig.system.defaults.CustomUserPreferences."com.brave.Browser";

  bookmarkBarIsForcedOnByPolicy = braveDarwinManagedPolicyKeys.BookmarkBarEnabled == true;
  googleSigninIsDisabledByPolicy = braveDarwinManagedPolicyKeys.BrowserSignin == 0;
  spellcheckRemoteServiceIsDisabledByPolicy =
    braveDarwinManagedPolicyKeys.SpellCheckServiceEnabled == false;
  spellcheckLanguageIsLockedToEnGbByPolicy =
    braveDarwinManagedPolicyKeys.SpellcheckLanguage == [ "en-GB" ];
  allPrivacySandboxApisAreDisabledByPolicy =
    braveDarwinManagedPolicyKeys.PrivacySandboxAdTopicsEnabled == false
    && braveDarwinManagedPolicyKeys.PrivacySandboxSiteEnabledAdsEnabled == false
    && braveDarwinManagedPolicyKeys.PrivacySandboxAdMeasurementEnabled == false;
  telemetryAndStatsPingsAreDisabledByPolicy =
    braveDarwinManagedPolicyKeys.MetricsReportingEnabled == false
    && braveDarwinManagedPolicyKeys.BraveStatsPingEnabled == false
    && braveDarwinManagedPolicyKeys.BraveP3AEnabled == false;
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
}
