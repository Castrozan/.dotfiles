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

  chromePersonalProfileLauncherDelegatesToChromeGlobal = lib.hasInfix "/bin/summon-chrome-global" chromeGlobalLauncher.chromePersonalProfileLauncherScript;

  chromePersonalProfileLauncherTargetsPersonalProfileDirectory = lib.hasInfix ''--profile-directory="Profile 2"'' chromeGlobalLauncher.chromePersonalProfileLauncherScript;

  chromePersonalProfileLauncherHasNoRemoteDebuggingFlag =
    !lib.hasInfix "--remote-debugging-port" chromeGlobalLauncher.chromePersonalProfileLauncherScript;

  chromePersonalProfileLauncherIsInHomePackages = lib.any (
    package: (lib.getName package) == "summon-chrome-personal-profile"
  ) chromeGlobalLauncherConfiguration.home.packages;

  chromeWorkProfileLauncherDelegatesToChromeGlobal = lib.hasInfix "/bin/summon-chrome-global" chromeGlobalLauncher.chromeWorkProfileLauncherScript;

  chromeWorkProfileLauncherTargetsWorkProfileDirectory = lib.hasInfix ''--profile-directory="Profile 1"'' chromeGlobalLauncher.chromeWorkProfileLauncherScript;

  chromeWorkProfileLauncherHasNoRemoteDebuggingFlag =
    !lib.hasInfix "--remote-debugging-port" chromeGlobalLauncher.chromeWorkProfileLauncherScript;

  chromeWorkProfileLauncherIsInHomePackages = lib.any (
    package: (lib.getName package) == "summon-chrome-work-profile"
  ) chromeGlobalLauncherConfiguration.home.packages;

  convergeActivationData =
    chromeGlobalLauncherConfiguration.home.activation.convergeChromeEntryPointsOnChromeGlobal.data;

  convergeActivationIsWired =
    chromeGlobalLauncherConfiguration.home.activation ? convergeChromeEntryPointsOnChromeGlobal;

  convergeActivationReferencesDuti = lib.hasInfix "/bin/duti" convergeActivationData;

  convergeActivationTargetsDefaultChromePath = lib.hasInfix "Library/Application Support/Google/Chrome" convergeActivationData;

  convergeActivationSetsPlainChromeBundleId = lib.hasInfix "com.google.Chrome" convergeActivationData;

  convergeScriptSource = builtins.readFile ../scripts/converge-chrome-entry-points-on-chrome-global.sh;

  convergeScriptSymlinksDefaultPathToChromeGlobal = lib.hasInfix ''ln -s "$chromeGlobalUserDataDirectory" "$defaultChromeUserDataDirectory"'' convergeScriptSource;

  convergeScriptDefersWhileChromeRuns = lib.hasInfix "pgrep -x" convergeScriptSource;

  convergeScriptBacksUpExistingDefaultProfile = lib.hasInfix "pre-chrome-global-symlink-backup" convergeScriptSource;

  convergeScriptSetsChromeAsDefaultBrowserViaDuti = lib.hasInfix ''"$dutiBinary" -s "$chromeBundleIdentifier" "$urlScheme"'' convergeScriptSource;

  convergeScriptRemovesRetiredLinkHandlerApp = lib.hasInfix ''rm -rf "$retiredLinkHandlerApplicationPath"'' convergeScriptSource;
in
{
  domain-desktop-chrome-global-launcher-targets-chrome-global-user-data-dir =
    mkEvalCheck "domain-desktop-chrome-global-launcher-targets-chrome-global-user-data-dir"
      chromeGlobalLauncherTargetsChromeGlobalUserDataDir
      "summon-chrome-global must launch the ~/.config/chrome-global profile, matching chromeGlobalUserDataDir in the chrome-devtools-mcp install so autoConnect can attach";

  domain-desktop-chrome-global-launcher-no-remote-debugging-flag =
    mkEvalCheck "domain-desktop-chrome-global-launcher-no-remote-debugging-flag"
      chromeGlobalLauncherHasNoRemoteDebuggingFlag
      "summon-chrome-global must not inject --remote-debugging-port so Chrome stays bare for autoConnect stealth, exposing the debug endpoint only through the in-Chrome consent dialog";

  domain-desktop-chrome-global-launcher-in-home-packages =
    mkEvalCheck "domain-desktop-chrome-global-launcher-in-home-packages"
      chromeGlobalLauncherIsInHomePackages
      "summon-chrome-global must be wired into home.packages so the launcher is on PATH for the chrome-devtools recovery step";

  domain-desktop-chrome-personal-profile-launcher-delegates-to-chrome-global =
    mkEvalCheck "domain-desktop-chrome-personal-profile-launcher-delegates-to-chrome-global"
      chromePersonalProfileLauncherDelegatesToChromeGlobal
      "summon-chrome-personal-profile must delegate to summon-chrome-global so it inherits the single ~/.config/chrome-global user-data-dir instead of forking a second Chrome data dir, which would open a stray profile store rather than a window in the live instance";

  domain-desktop-chrome-personal-profile-launcher-targets-personal-profile-directory =
    mkEvalCheck "domain-desktop-chrome-personal-profile-launcher-targets-personal-profile-directory"
      chromePersonalProfileLauncherTargetsPersonalProfileDirectory
      "summon-chrome-personal-profile must pass --profile-directory=\"Profile 2\" so the Cmd+B summon opens the personal profile window, not the work profile";

  domain-desktop-chrome-personal-profile-launcher-no-remote-debugging-flag =
    mkEvalCheck "domain-desktop-chrome-personal-profile-launcher-no-remote-debugging-flag"
      chromePersonalProfileLauncherHasNoRemoteDebuggingFlag
      "summon-chrome-personal-profile must not inject --remote-debugging-port so the personal profile stays a bare browser like the global launcher";

  domain-desktop-chrome-personal-profile-launcher-in-home-packages =
    mkEvalCheck "domain-desktop-chrome-personal-profile-launcher-in-home-packages"
      chromePersonalProfileLauncherIsInHomePackages
      "summon-chrome-personal-profile must be wired into home.packages so the hammerspoon Cmd+B cold-launch resolves it on PATH";

  domain-desktop-chrome-work-profile-launcher-delegates-to-chrome-global =
    mkEvalCheck "domain-desktop-chrome-work-profile-launcher-delegates-to-chrome-global"
      chromeWorkProfileLauncherDelegatesToChromeGlobal
      "summon-chrome-work-profile must delegate to summon-chrome-global so it inherits the single ~/.config/chrome-global user-data-dir instead of forking a second Chrome data dir, which would open a stray profile store rather than a window in the live instance";

  domain-desktop-chrome-work-profile-launcher-targets-work-profile-directory =
    mkEvalCheck "domain-desktop-chrome-work-profile-launcher-targets-work-profile-directory"
      chromeWorkProfileLauncherTargetsWorkProfileDirectory
      "summon-chrome-work-profile must pass --profile-directory=\"Profile 1\" so the Cmd+C summon opens the work profile window, not the personal profile";

  domain-desktop-chrome-work-profile-launcher-no-remote-debugging-flag =
    mkEvalCheck "domain-desktop-chrome-work-profile-launcher-no-remote-debugging-flag"
      chromeWorkProfileLauncherHasNoRemoteDebuggingFlag
      "summon-chrome-work-profile must not inject --remote-debugging-port so the work profile stays a bare browser like the global launcher";

  domain-desktop-chrome-work-profile-launcher-in-home-packages =
    mkEvalCheck "domain-desktop-chrome-work-profile-launcher-in-home-packages"
      chromeWorkProfileLauncherIsInHomePackages
      "summon-chrome-work-profile must be wired into home.packages so the hammerspoon Cmd+C cold-launch resolves it on PATH";

  domain-desktop-chrome-converge-activation-wired =
    mkEvalCheck "domain-desktop-chrome-converge-activation-wired" convergeActivationIsWired
      "the convergeChromeEntryPointsOnChromeGlobal activation must be wired so every macOS Chrome entry point resolves to the single chrome-global profile";

  domain-desktop-chrome-converge-activation-references-duti =
    mkEvalCheck "domain-desktop-chrome-converge-activation-references-duti"
      convergeActivationReferencesDuti
      "forcing the activation must resolve the darwin-only duti store path, proving the module evaluates under darwin pkgs in the test harness instead of passing only because the wired-check never forced the thunk";

  domain-desktop-chrome-converge-activation-targets-default-path =
    mkEvalCheck "domain-desktop-chrome-converge-activation-targets-default-path"
      convergeActivationTargetsDefaultChromePath
      "the activation must pass Chrome's default macOS user-data-dir so the symlink is placed where an unflagged Chrome launch (Dock, Spotlight, Finder) actually looks";

  domain-desktop-chrome-converge-activation-sets-plain-chrome-default =
    mkEvalCheck "domain-desktop-chrome-converge-activation-sets-plain-chrome-default"
      convergeActivationSetsPlainChromeBundleId
      "the activation must pass the plain com.google.Chrome bundle id so links route through Chrome itself, not the retired AppleScript link-handler applet that showed a startup-screen splash";

  domain-desktop-chrome-converge-symlinks-default-path-to-chrome-global =
    mkEvalCheck "domain-desktop-chrome-converge-symlinks-default-path-to-chrome-global"
      convergeScriptSymlinksDefaultPathToChromeGlobal
      "the script must symlink the default profile path to chrome-global so every launch path resolves to the single configured profile";

  domain-desktop-chrome-converge-defers-while-chrome-runs =
    mkEvalCheck "domain-desktop-chrome-converge-defers-while-chrome-runs"
      convergeScriptDefersWhileChromeRuns
      "the script must defer while Chrome is running so it never swaps the profile directory or the default browser out from under an open instance, and so the symlink and the duti switch land together with no regression window";

  domain-desktop-chrome-converge-backs-up-existing-profile =
    mkEvalCheck "domain-desktop-chrome-converge-backs-up-existing-profile"
      convergeScriptBacksUpExistingDefaultProfile
      "the script must back up a pre-existing real default profile once before replacing it with the symlink so no profile data is destroyed";

  domain-desktop-chrome-converge-sets-chrome-default-browser-via-duti =
    mkEvalCheck "domain-desktop-chrome-converge-sets-chrome-default-browser-via-duti"
      convergeScriptSetsChromeAsDefaultBrowserViaDuti
      "the script must register plain Chrome as the default http and https handler via duti so link clicks open Chrome directly into the symlinked chrome-global profile";

  domain-desktop-chrome-converge-removes-retired-link-handler-app =
    mkEvalCheck "domain-desktop-chrome-converge-removes-retired-link-handler-app"
      convergeScriptRemovesRetiredLinkHandlerApp
      "the script must remove the retired Chrome Global Link Handler applet so the stale AppleScript app no longer lingers once plain Chrome is the default browser";
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
