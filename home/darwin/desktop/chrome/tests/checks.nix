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

  linkDefaultChromeProfileActivationIsWired =
    chromeGlobalLauncherConfiguration.home.activation ? linkDefaultChromeProfileToChromeGlobalProfile;

  linkDefaultChromeProfileActivationTargetsDefaultChromePath = lib.hasInfix "Library/Application Support/Google/Chrome" chromeGlobalLauncherConfiguration.home.activation.linkDefaultChromeProfileToChromeGlobalProfile.data;

  linkDefaultChromeProfileScriptSource = builtins.readFile ../scripts/link-default-chrome-profile-to-chrome-global.sh;

  linkDefaultChromeProfileScriptSymlinksDefaultPathToChromeGlobal = lib.hasInfix ''ln -s "$chromeGlobalUserDataDirectory" "$defaultChromeUserDataDirectory"'' linkDefaultChromeProfileScriptSource;

  linkDefaultChromeProfileScriptDefersWhileChromeRuns = lib.hasInfix "pgrep -x" linkDefaultChromeProfileScriptSource;

  linkDefaultChromeProfileScriptBacksUpExistingDefaultProfile = lib.hasInfix "pre-chrome-global-symlink-backup" linkDefaultChromeProfileScriptSource;
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

  domain-desktop-chrome-link-default-profile-activation-wired =
    mkEvalCheck "domain-desktop-chrome-link-default-profile-activation-wired"
      linkDefaultChromeProfileActivationIsWired
      "the linkDefaultChromeProfileToChromeGlobalProfile activation must be wired so the raw Chrome.app launch path (Dock, Spotlight, manual open) shares the one chrome-global profile instead of Chrome's untouched default profile";

  domain-desktop-chrome-link-default-profile-activation-targets-default-path =
    mkEvalCheck "domain-desktop-chrome-link-default-profile-activation-targets-default-path"
      linkDefaultChromeProfileActivationTargetsDefaultChromePath
      "the activation must pass Chrome's default macOS user-data-dir so the symlink is placed where an unflagged Chrome launch actually looks";

  domain-desktop-chrome-link-default-profile-symlinks-to-chrome-global =
    mkEvalCheck "domain-desktop-chrome-link-default-profile-symlinks-to-chrome-global"
      linkDefaultChromeProfileScriptSymlinksDefaultPathToChromeGlobal
      "the script must symlink the default profile path to chrome-global so every launch path resolves to the single configured profile";

  domain-desktop-chrome-link-default-profile-defers-while-chrome-runs =
    mkEvalCheck "domain-desktop-chrome-link-default-profile-defers-while-chrome-runs"
      linkDefaultChromeProfileScriptDefersWhileChromeRuns
      "the script must defer while Chrome is running so it never swaps the profile directory out from under an open instance";

  domain-desktop-chrome-link-default-profile-backs-up-existing-profile =
    mkEvalCheck "domain-desktop-chrome-link-default-profile-backs-up-existing-profile"
      linkDefaultChromeProfileScriptBacksUpExistingDefaultProfile
      "the script must back up a pre-existing real default profile once before replacing it with the symlink so no profile data is destroyed";
}
// import ./checks/preferences-overrides-checks.nix {
  inherit
    pkgs
    lib
    inputs
    nixpkgs-version
    home-version
    ;
}
