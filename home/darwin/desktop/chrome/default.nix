{
  pkgs,
  config,
  ...
}:
let
  chromiumProfilePreferenceMerge = import ../chromium-preferences/profile-preference-merge.nix {
    inherit pkgs;
  };
in
{
  home.activation.mergeChromeDefaultProfilePreferences =
    config.lib.dag.entryAfter
      [
        "writeBoundary"
      ]
      (
        chromiumProfilePreferenceMerge.mkChromiumProfilePreferenceMergeActivationScript {
          browserDisplayProcessName = "Google Chrome";
          browserUserDataDirectoryRelativeToHome = "Library/Application Support/Google/Chrome";
          preferencesOverridesJsonFile = ./preferences-overrides.json;
          sentinelBasename = "chrome-preferences-applied";
        }
      );
}
