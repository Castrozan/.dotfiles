{
  pkgs,
  lib,
  inputs,
  nixpkgs-version,
  home-version,
}:
let
  helpers = import ../../../../../../__tests__/nix-checks/helpers.nix {
    inherit
      pkgs
      lib
      inputs
      nixpkgs-version
      home-version
      ;
  };
  inherit (helpers) mkEvalCheck;

  chromeGlobalLauncherConfiguration = helpers.homeManagerTestConfigurationForDarwin [
    ../../default.nix
  ];

  convergeActivationData =
    chromeGlobalLauncherConfiguration.home.activation.convergeChromeEntryPointsOnChromeGlobal.data;

  convergeActivationIsWired =
    chromeGlobalLauncherConfiguration.home.activation ? convergeChromeEntryPointsOnChromeGlobal;

  convergeActivationReferencesDuti = lib.hasInfix "/bin/duti" convergeActivationData;

  convergeActivationTargetsDefaultChromePath = lib.hasInfix "Library/Application Support/Google/Chrome" convergeActivationData;

  convergeActivationSetsPlainChromeBundleId = lib.hasInfix "com.google.Chrome" convergeActivationData;

  convergeScriptSource = builtins.readFile ../../scripts/converge-chrome-entry-points-on-chrome-global.sh;

  convergeScriptSymlinksDefaultPathToChromeGlobal = lib.hasInfix ''ln -s "$chromeGlobalUserDataDirectory" "$defaultChromeUserDataDirectory"'' convergeScriptSource;

  convergeScriptDefersWhileChromeRuns = lib.hasInfix "pgrep -x" convergeScriptSource;

  convergeScriptBacksUpExistingDefaultProfile = lib.hasInfix "pre-chrome-global-symlink-backup" convergeScriptSource;

  convergeScriptSetsChromeAsDefaultBrowserViaDuti = lib.hasInfix ''"$dutiBinary" -s "$chromeBundleIdentifier" "$urlScheme"'' convergeScriptSource;

  convergeScriptRemovesRetiredLinkHandlerApp = lib.hasInfix ''rm -rf "$retiredLinkHandlerApplicationPath"'' convergeScriptSource;

  convergeScriptSourceBeforeChromeRunningGuard = lib.head (
    lib.splitString "pgrep -x" convergeScriptSource
  );

  convergeScriptSourceAfterChromeRunningGuard = lib.last (
    lib.splitString "pgrep -x" convergeScriptSource
  );

  convergeScriptSetsChromeDefaultBrowserBeforeChromeRunningGuard = lib.hasInfix ''"$dutiBinary" -s "$chromeBundleIdentifier" "$urlScheme"'' convergeScriptSourceBeforeChromeRunningGuard;

  convergeScriptRemovesRetiredLinkHandlerAppBeforeChromeRunningGuard = lib.hasInfix ''rm -rf "$retiredLinkHandlerApplicationPath"'' convergeScriptSourceBeforeChromeRunningGuard;

  convergeScriptGatesSymlinkSwapBehindChromeRunningGuard = lib.hasInfix ''ln -s "$chromeGlobalUserDataDirectory" "$defaultChromeUserDataDirectory"'' convergeScriptSourceAfterChromeRunningGuard;
in
{
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
      "the script must gate the profile-directory symlink swap behind a Chrome-running check so it never backs up or replaces a profile directory out from under an open instance";

  domain-desktop-chrome-converge-sets-default-browser-before-chrome-running-guard =
    mkEvalCheck "domain-desktop-chrome-converge-sets-default-browser-before-chrome-running-guard"
      convergeScriptSetsChromeDefaultBrowserBeforeChromeRunningGuard
      "the duti default-browser switch must run before the Chrome-running guard so a machine whose Chrome never stops during a rebuild still converges its default browser onto plain Chrome, instead of leaving the retired AppleScript link-handler registered forever and showing its startup-screen dialog on every link click";

  domain-desktop-chrome-converge-removes-retired-app-before-chrome-running-guard =
    mkEvalCheck "domain-desktop-chrome-converge-removes-retired-app-before-chrome-running-guard"
      convergeScriptRemovesRetiredLinkHandlerAppBeforeChromeRunningGuard
      "the retired link-handler applet removal must run before the Chrome-running guard so the stale AppleScript app is deleted even on an always-on-Chrome machine, right after duti repoints http and https at plain Chrome";

  domain-desktop-chrome-converge-gates-symlink-swap-behind-chrome-running-guard =
    mkEvalCheck "domain-desktop-chrome-converge-gates-symlink-swap-behind-chrome-running-guard"
      convergeScriptGatesSymlinkSwapBehindChromeRunningGuard
      "the profile-directory symlink swap must stay after the Chrome-running guard because backing up and replacing the default user-data-dir is the only step unsafe to run under a live Chrome, unlike the duti switch and the applet removal";

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
