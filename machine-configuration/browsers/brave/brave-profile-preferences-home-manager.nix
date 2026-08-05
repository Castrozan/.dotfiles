{
  pkgs,
  config,
  ...
}:
let
  chromiumProfilePreferenceMerge =
    import ../chromium-profile-preferences/chromium-profile-preference-merge.nix
      {
        inherit pkgs;
      };
  braveDefaultProfile = import ./brave-default-profile.nix {
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
          preferencesOverridesJsonFile = ./program-configuration/preferences-overrides.json;
          sentinelBasename = "brave-preferences-applied";
        }
      );
}
