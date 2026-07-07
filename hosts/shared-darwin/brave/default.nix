{ lib, ... }:
let
  braveUpdaterUpdatesDisabledManagedPreferencePlist = lib.generators.toPlist { escape = true; } {
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
    printf '%s' ${lib.escapeShellArg braveUpdaterUpdatesDisabledManagedPreferencePlist} > "/Library/Managed Preferences/com.brave.Keystone.plist"
    /bin/chmod 0644 "/Library/Managed Preferences/com.brave.Keystone.plist"
  '';

  system.defaults.CustomUserPreferences."com.brave.Browser" = {
    BookmarkBarEnabled = true;
    BrowserSignin = 0;
    PasswordManagerEnabled = false;
    SpellCheckServiceEnabled = false;
    SpellcheckLanguage = [ "en-GB" ];
    PrivacySandboxAdTopicsEnabled = false;
    PrivacySandboxSiteEnabledAdsEnabled = false;
    PrivacySandboxAdMeasurementEnabled = false;
    MetricsReportingEnabled = false;
    BraveStatsPingEnabled = false;
    BraveP3AEnabled = false;
    SUEnableAutomaticChecks = false;
    SUAutomaticallyUpdate = false;
  };
}
