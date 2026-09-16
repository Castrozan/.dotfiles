{
  DisableTelemetry = true;
  DisableFirefoxStudies = true;
  DisablePocket = true;
  DisableFirefoxAccounts = false;
  DisableSetDesktopBackground = true;
  DisplayBookmarksToolbar = "newtab";
  DontCheckDefaultBrowser = true;
  EnableTrackingProtection = {
    Value = true;
    Locked = true;
    Cryptomining = true;
    Fingerprinting = true;
    EmailTracking = true;
  };
  OfferToSaveLogins = false;
  PasswordManagerEnabled = false;
  FirefoxHome = {
    Search = true;
    TopSites = false;
    SponsoredTopSites = false;
    Highlights = false;
    Pocket = false;
    SponsoredPocket = false;
    Snippets = false;
  };
  FirefoxSuggest = {
    WebSuggestions = false;
    SponsoredSuggestions = false;
    ImproveSuggest = false;
  };
  UserMessaging = {
    ExtensionRecommendations = false;
    FeatureRecommendations = false;
    SkipOnboarding = true;
  };
  HttpsOnlyMode = "enabled";
  ExtensionSettings = {
    "uBlock0@raymondhill.net" = {
      install_url = "https://addons.mozilla.org/firefox/downloads/latest/ublock-origin/latest.xpi";
      installation_mode = "force_installed";
    };

    "jid1-MnnxcxisBPnSXQ@jetpack" = {
      install_url = "https://addons.mozilla.org/firefox/downloads/latest/privacy-badger17/latest.xpi";
      installation_mode = "force_installed";
    };
    "addon@darkreader.org" = {
      install_url = "https://addons.mozilla.org/firefox/downloads/latest/darkreader/latest.xpi";
      installation_mode = "force_installed";
    };
  };
}
