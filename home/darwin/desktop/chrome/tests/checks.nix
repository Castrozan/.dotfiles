{
  pkgs,
  lib,
  inputs,
  nixpkgs-version,
  home-version,
}:
let
  helpers = import ../../../../../tests/nix-checks/helpers.nix {
    inherit
      pkgs
      lib
      inputs
      nixpkgs-version
      home-version
      ;
  };
  inherit (helpers) mkEvalCheck;

  chromePreferencesOverrides = builtins.fromJSON (builtins.readFile ../preferences-overrides.json);

  chromeBookmarkBarShownOnAllTabs = chromePreferencesOverrides.bookmark_bar.show_on_all_tabs;

  chromeThemeColorSchemeIsDark = chromePreferencesOverrides.browser.theme.color_scheme == 2;

  chromeSpellcheckIsLockedToEnGb = chromePreferencesOverrides.spellcheck.dictionaries == [ "en-GB" ];

  chromeAcceptLanguagesMatchBrave =
    chromePreferencesOverrides.intl.accept_languages == "en-US,pt-BR,pt,en";

  chromePrivacySandboxTopicsDisabled = !chromePreferencesOverrides.privacy_sandbox.m1.topics_enabled;

  chromeKeepsGoogleSigninEnabledByOmittingTheSigninOverride = !(chromePreferencesOverrides ? signin);

  chromeOmitsBraveSpecificNamespace = !(chromePreferencesOverrides ? brave);

  chromeOmitsBraveSearchProviderGuid = !(chromePreferencesOverrides ? default_search_provider);
in
{
  domain-desktop-chrome-bookmark-bar-shown-on-all-tabs =
    mkEvalCheck "domain-desktop-chrome-bookmark-bar-shown-on-all-tabs" chromeBookmarkBarShownOnAllTabs
      "Chrome bookmark_bar.show_on_all_tabs must be true to mirror the Brave bookmark bar";

  domain-desktop-chrome-theme-color-scheme-is-dark =
    mkEvalCheck "domain-desktop-chrome-theme-color-scheme-is-dark" chromeThemeColorSchemeIsDark
      "Chrome browser.theme.color_scheme must be 2 (dark) to mirror the Brave dark theme";

  domain-desktop-chrome-spellcheck-locked-to-en-gb =
    mkEvalCheck "domain-desktop-chrome-spellcheck-locked-to-en-gb" chromeSpellcheckIsLockedToEnGb
      "Chrome spellcheck.dictionaries must contain exactly en-GB to mirror Brave";

  domain-desktop-chrome-accept-languages-match-brave =
    mkEvalCheck "domain-desktop-chrome-accept-languages-match-brave" chromeAcceptLanguagesMatchBrave
      "Chrome intl.accept_languages must match the Brave language order en-US,pt-BR,pt,en";

  domain-desktop-chrome-privacy-sandbox-topics-disabled =
    mkEvalCheck "domain-desktop-chrome-privacy-sandbox-topics-disabled"
      chromePrivacySandboxTopicsDisabled
      "Chrome privacy_sandbox.m1.topics_enabled must be false to mirror Brave's privacy sandbox lockdown";

  domain-desktop-chrome-google-signin-stays-enabled =
    mkEvalCheck "domain-desktop-chrome-google-signin-stays-enabled"
      chromeKeepsGoogleSigninEnabledByOmittingTheSigninOverride
      "Chrome overrides must omit the signin key so Google sign-in stays enabled, unlike the Brave overrides which disable it";

  domain-desktop-chrome-omits-brave-specific-namespace =
    mkEvalCheck "domain-desktop-chrome-omits-brave-specific-namespace" chromeOmitsBraveSpecificNamespace
      "Chrome overrides must omit the brave namespace because Chrome ignores brave.accelerators and brave button-visibility keys";

  domain-desktop-chrome-omits-brave-search-provider-guid =
    mkEvalCheck "domain-desktop-chrome-omits-brave-search-provider-guid"
      chromeOmitsBraveSearchProviderGuid
      "Chrome overrides must omit default_search_provider because the Brave prepopulated-engine guid does not match Chrome's TemplateURL guids and Google is already Chrome's default";
}
