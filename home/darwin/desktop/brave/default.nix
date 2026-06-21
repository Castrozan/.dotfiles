{
  pkgs,
  config,
  ...
}:
let
  chromiumProfilePreferenceMerge = import ../chromium-preferences/profile-preference-merge.nix {
    inherit pkgs;
  };
  braveDefaultProfile = import ../../../base/browser/brave-default-profile.nix {
    isDarwin = true;
  };
in
{
  home.activation.mergeBraveDefaultProfilePreferences =
    config.lib.dag.entryAfter
      [
        "writeBoundary"
      ]
      (
        chromiumProfilePreferenceMerge.mkChromiumProfilePreferenceMergeActivationScript {
          browserDisplayProcessName = "Brave Browser";
          browserUserDataDirectoryRelativeToHome = braveDefaultProfile.userDataDirectoryRelativeToHome;
          preferencesOverridesJsonFile = ./preferences-overrides.json;
          sentinelBasename = "brave-preferences-applied";
        }
      );
}
