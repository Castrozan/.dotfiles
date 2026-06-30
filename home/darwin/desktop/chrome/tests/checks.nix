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

  chromeGlobalLauncherConfiguration = helpers.homeManagerTestConfigurationForDarwin [
    ../default.nix
  ];

  chromeGlobalLauncherTargetsChromeGlobalUserDataDir = lib.hasInfix ''--user-data-dir="$HOME/.config/chrome-global"'' chromeGlobalLauncher.chromeGlobalLauncherScript;

  chromeGlobalLauncherHasNoRemoteDebuggingFlag =
    !lib.hasInfix "--remote-debugging-port" chromeGlobalLauncher.chromeGlobalLauncherScript;

  chromeGlobalLauncherIsInHomePackages = lib.any (
    package: (lib.getName package) == "summon-chrome-global"
  ) chromeGlobalLauncherConfiguration.home.packages;

  chromeGlobalUrlOpenerTargetsChromeGlobalUserDataDir = lib.hasInfix ''--user-data-dir="$HOME/.config/chrome-global"'' chromeGlobalLauncher.chromeGlobalUrlOpenerScript;

  chromeGlobalUrlOpenerIsInHomePackages = lib.any (
    package: (lib.getName package) == "open-url-in-chrome-global"
  ) chromeGlobalLauncherConfiguration.home.packages;

  defaultBrowserHandlerActivationIsWired =
    chromeGlobalLauncherConfiguration.home.activation ? installChromeGlobalDefaultBrowserHandler;

  defaultBrowserHandlerActivationReferencesDuti = lib.hasInfix "/bin/duti" chromeGlobalLauncherConfiguration.home.activation.installChromeGlobalDefaultBrowserHandler.data;

  installDefaultBrowserHandlerScriptSource = builtins.readFile ../scripts/install-chrome-global-default-browser-handler.sh;

  installDefaultBrowserHandlerScriptUsesOpenLocationHandler = lib.hasInfix "on open location" installDefaultBrowserHandlerScriptSource;

  installDefaultBrowserHandlerScriptDeclaresHttpAndHttpsSchemes =
    lib.hasInfix "CFBundleURLSchemes:0 string http" installDefaultBrowserHandlerScriptSource
    && lib.hasInfix "CFBundleURLSchemes:1 string https" installDefaultBrowserHandlerScriptSource;

  installDefaultBrowserHandlerScriptRegistersDefaultViaDuti =
    lib.hasInfix "for urlScheme in http https" installDefaultBrowserHandlerScriptSource
    && lib.hasInfix ''"$dutiBinary" -s "$handlerBundleIdentifier" "$urlScheme"'' installDefaultBrowserHandlerScriptSource;

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

  domain-desktop-chrome-global-url-opener-targets-chrome-global-user-data-dir =
    mkEvalCheck "domain-desktop-chrome-global-url-opener-targets-chrome-global-user-data-dir"
      chromeGlobalUrlOpenerTargetsChromeGlobalUserDataDir
      "open-url-in-chrome-global must open URLs in the ~/.config/chrome-global profile so links land in the attachable chrome-devtools-mcp target, not the unreachable default profile";

  domain-desktop-chrome-global-url-opener-in-home-packages =
    mkEvalCheck "domain-desktop-chrome-global-url-opener-in-home-packages"
      chromeGlobalUrlOpenerIsInHomePackages
      "open-url-in-chrome-global must be wired into home.packages so the default-browser handler app can forward URLs to it by absolute store path";

  domain-desktop-chrome-global-default-browser-handler-activation-wired =
    mkEvalCheck "domain-desktop-chrome-global-default-browser-handler-activation-wired"
      defaultBrowserHandlerActivationIsWired
      "the installChromeGlobalDefaultBrowserHandler activation must be wired so darwin reaches parity with the Linux xdg.mimeApps routing that already sends links to chrome-global";

  domain-desktop-chrome-global-default-browser-handler-activation-references-duti =
    mkEvalCheck "domain-desktop-chrome-global-default-browser-handler-activation-references-duti"
      defaultBrowserHandlerActivationReferencesDuti
      "forcing the activation script must resolve the darwin-only duti store path, proving the module evaluates under darwin pkgs in the test harness instead of passing only because the wired-check never forces the thunk";

  domain-desktop-chrome-global-default-browser-handler-uses-open-location =
    mkEvalCheck "domain-desktop-chrome-global-default-browser-handler-uses-open-location"
      installDefaultBrowserHandlerScriptUsesOpenLocationHandler
      "the handler app must implement the AppleScript open-location handler because LaunchServices delivers http/https to a default browser via the GURL Apple event, not argv";

  domain-desktop-chrome-global-default-browser-handler-declares-http-https =
    mkEvalCheck "domain-desktop-chrome-global-default-browser-handler-declares-http-https"
      installDefaultBrowserHandlerScriptDeclaresHttpAndHttpsSchemes
      "the handler app Info.plist must declare http and https CFBundleURLSchemes or LaunchServices will not offer it as a default web browser";

  domain-desktop-chrome-global-default-browser-handler-registers-via-duti =
    mkEvalCheck "domain-desktop-chrome-global-default-browser-handler-registers-via-duti"
      installDefaultBrowserHandlerScriptRegistersDefaultViaDuti
      "the install script must set the handler as the default http and https handler via duti so link clicks route to chrome-global";

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
