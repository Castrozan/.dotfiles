{
  pkgs,
  config,
  ...
}:
let
  chromiumProfilePreferenceMerge = import ../chromium-preferences/profile-preference-merge.nix {
    inherit pkgs;
  };

  chromeGlobalLauncher = import ./chrome-global-launcher.nix { inherit pkgs; };

  convergeChromeEntryPointsOnChromeGlobalScript = ./scripts/converge-chrome-entry-points-on-chrome-global.sh;
  chromeBundleIdentifier = "com.google.Chrome";
  retiredChromeGlobalLinkHandlerApplicationName = "Chrome Global Link Handler";
in
{
  home = {
    packages = [
      chromeGlobalLauncher.chromeGlobalLauncherPackage
      chromeGlobalLauncher.chromePersonalProfileLauncherPackage
      chromeGlobalLauncher.chromeWorkProfileLauncherPackage
    ];

    activation = {
      mergeChromeGlobalProfilePreferences =
        config.lib.dag.entryAfter
          [
            "writeBoundary"
          ]
          (
            chromiumProfilePreferenceMerge.mkChromiumProfilePreferenceMergeActivationScript {
              browserDisplayProcessName = "Google Chrome";
              browserUserDataDirectoryRelativeToHome = ".config/chrome-global";
              preferencesOverridesJsonFile = ./preferences-overrides.json;
              sentinelBasename = "chrome-global-preferences-applied";
            }
          );

      applyChromeGlobalPersonalProfileDistinctiveIcon =
        config.lib.dag.entryAfter
          [
            "writeBoundary"
          ]
          (
            chromiumProfilePreferenceMerge.mkChromiumProfilePreferenceMergeActivationScript {
              browserDisplayProcessName = "Google Chrome";
              browserUserDataDirectoryRelativeToHome = ".config/chrome-global";
              preferencesOverridesJsonFile = ./local-state-personal-profile-overrides.json;
              sentinelBasename = "chrome-global-personal-profile-icon-applied";
              targetFileRelativeToUserDataDirectory = "Local State";
            }
          );

      convergeChromeEntryPointsOnChromeGlobal =
        config.lib.dag.entryAfter
          [
            "writeBoundary"
          ]
          ''
            ${pkgs.bash}/bin/bash ${convergeChromeEntryPointsOnChromeGlobalScript} \
              "$HOME/${chromeGlobalLauncher.chromeGlobalUserDataDirectoryRelativeToHome}" \
              "$HOME/Library/Application Support/Google/Chrome" \
              "Google Chrome" \
              "${pkgs.duti}/bin/duti" \
              "${chromeBundleIdentifier}" \
              "$HOME/Applications/${retiredChromeGlobalLinkHandlerApplicationName}.app" || echo "WARN: chrome-global entry-point convergence failed; a later rebuild retries." >&2
          '';
    };
  };
}
