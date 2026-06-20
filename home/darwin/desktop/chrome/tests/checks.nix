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

  chromeGlobalLauncher = import ../chrome-global-launcher.nix { inherit pkgs; };

  chromeGlobalLauncherConfiguration = helpers.homeManagerTestConfiguration [ ../default.nix ];

  chromeGlobalLauncherTargetsChromeGlobalUserDataDir = lib.hasInfix ''--user-data-dir="$HOME/.config/chrome-global"'' chromeGlobalLauncher.chromeGlobalLauncherScript;

  chromeGlobalLauncherHasNoRemoteDebuggingFlag =
    !lib.hasInfix "--remote-debugging-port" chromeGlobalLauncher.chromeGlobalLauncherScript;

  chromeGlobalLauncherIsInHomePackages = lib.any (
    package: (lib.getName package) == "summon-chrome-global"
  ) chromeGlobalLauncherConfiguration.home.packages;

  chromePreferencesOverrides = builtins.fromJSON (builtins.readFile ../preferences-overrides.json);

  chromeBookmarkBarShownOnAllTabs = chromePreferencesOverrides.bookmark_bar.show_on_all_tabs;

  chromeThemeColorSchemeIsDark = chromePreferencesOverrides.browser.theme.color_scheme == 2;

  chromePrivacySandboxTopicsDisabled = !chromePreferencesOverrides.privacy_sandbox.m1.topics_enabled;

  chromeKeepsGoogleSigninEnabledByOmittingTheSigninOverride = !(chromePreferencesOverrides ? signin);

  chromeOmitsBraveSpecificNamespace = !(chromePreferencesOverrides ? brave);

  chromeOmitsBraveSearchProviderGuid = !(chromePreferencesOverrides ? default_search_provider);

  chromeOmitsSpellcheckOverrideChromeRevertsOnLaunch = !(chromePreferencesOverrides ? spellcheck);

  chromeOmitsIntlLanguageOverrideChromeRevertsOnLaunch = !(chromePreferencesOverrides ? intl);
in
{
  domain-desktop-chrome-global-launcher-targets-chrome-global-user-data-dir =
    mkEvalCheck "domain-desktop-chrome-global-launcher-targets-chrome-global-user-data-dir"
      chromeGlobalLauncherTargetsChromeGlobalUserDataDir
      "summon-chrome-global must launch the non-default ~/.config/chrome-global profile, matching chromeGlobalUserDataDir in the chrome-devtools-mcp install so autoConnect can attach";

  domain-desktop-chrome-global-launcher-no-remote-debugging-flag =
    mkEvalCheck "domain-desktop-chrome-global-launcher-no-remote-debugging-flag"
      chromeGlobalLauncherHasNoRemoteDebuggingFlag
      "summon-chrome-global must not inject --remote-debugging-port so Chrome stays bare for autoConnect stealth, exposing the debug endpoint only through the in-Chrome consent dialog";

  domain-desktop-chrome-global-launcher-in-home-packages =
    mkEvalCheck "domain-desktop-chrome-global-launcher-in-home-packages"
      chromeGlobalLauncherIsInHomePackages
      "summon-chrome-global must be wired into home.packages so the launcher is on PATH for the chrome-devtools recovery step";

  domain-desktop-chrome-bookmark-bar-shown-on-all-tabs =
    mkEvalCheck "domain-desktop-chrome-bookmark-bar-shown-on-all-tabs" chromeBookmarkBarShownOnAllTabs
      "Chrome bookmark_bar.show_on_all_tabs must be true to mirror the Brave bookmark bar";

  domain-desktop-chrome-theme-color-scheme-is-dark =
    mkEvalCheck "domain-desktop-chrome-theme-color-scheme-is-dark" chromeThemeColorSchemeIsDark
      "Chrome browser.theme.color_scheme must be 2 (dark) to mirror the Brave dark theme";

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

  domain-desktop-chrome-omits-spellcheck-override =
    mkEvalCheck "domain-desktop-chrome-omits-spellcheck-override"
      chromeOmitsSpellcheckOverrideChromeRevertsOnLaunch
      "Chrome overrides must omit spellcheck because Chrome reconciles spellcheck dictionaries on launch and reverts an external file write, so pinning it here is a no-op";

  domain-desktop-chrome-omits-intl-language-override =
    mkEvalCheck "domain-desktop-chrome-omits-intl-language-override"
      chromeOmitsIntlLanguageOverrideChromeRevertsOnLaunch
      "Chrome overrides must omit intl because Chrome reconciles accept_languages on launch and reverts an external file write, so pinning it here is a no-op";
}
