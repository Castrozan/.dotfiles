{
  pkgs,
  lib,
  inputs,
  nixpkgs-version,
  home-version,
}:
let
  helpers = import ../../../../../../tests/nix-checks/helpers.nix {
    inherit
      pkgs
      lib
      inputs
      nixpkgs-version
      home-version
      ;
  };
  inherit (helpers) mkEvalCheck;

  personalProfileIconOverrides = builtins.fromJSON (
    builtins.readFile ../../local-state-personal-profile-overrides.json
  );

  personalProfileOverrides = personalProfileIconOverrides.profile.info_cache."Profile 2";

  iconOverridesTargetPersonalProfileDirectory =
    personalProfileIconOverrides.profile.info_cache ? "Profile 2";

  iconOverridesSetAvatarIcon = personalProfileOverrides ? avatar_icon;

  iconOverridesDisableGaiaPicture = personalProfileOverrides.use_gaia_picture == false;

  chromeConfiguration = helpers.homeManagerTestConfigurationForDarwin [
    ../../default.nix
  ];

  iconActivationIsWired =
    chromeConfiguration.home.activation ? applyChromeGlobalPersonalProfileDistinctiveIcon;

  iconActivationData =
    chromeConfiguration.home.activation.applyChromeGlobalPersonalProfileDistinctiveIcon.data;

  iconActivationTargetsLocalState = lib.hasInfix "Local State" iconActivationData;
in
{
  domain-desktop-chrome-personal-profile-icon-overrides-target-personal-profile =
    mkEvalCheck "domain-desktop-chrome-personal-profile-icon-overrides-target-personal-profile"
      iconOverridesTargetPersonalProfileDirectory
      "the icon overrides must key the personal profile directory (Profile 2) under profile.info_cache so the distinctive avatar lands on personal, not the work profile that shares the same avatar and gray highlight";

  domain-desktop-chrome-personal-profile-icon-overrides-set-avatar =
    mkEvalCheck "domain-desktop-chrome-personal-profile-icon-overrides-set-avatar"
      iconOverridesSetAvatarIcon
      "the icon overrides must set avatar_icon so the personal profile shows a distinctive built-in avatar instead of the default IDR_PROFILE_AVATAR_26 both profiles otherwise share";

  domain-desktop-chrome-personal-profile-icon-overrides-disable-gaia-picture =
    mkEvalCheck "domain-desktop-chrome-personal-profile-icon-overrides-disable-gaia-picture"
      iconOverridesDisableGaiaPicture
      "the icon overrides must set use_gaia_picture false so the chosen avatar_icon actually renders, because Chrome shows the Google account photo over avatar_icon whenever use_gaia_picture is true";

  domain-desktop-chrome-personal-profile-icon-activation-wired =
    mkEvalCheck "domain-desktop-chrome-personal-profile-icon-activation-wired" iconActivationIsWired
      "the applyChromeGlobalPersonalProfileDistinctiveIcon activation must be wired so a rebuild merges the distinctive avatar into the profile info cache";

  domain-desktop-chrome-personal-profile-icon-activation-targets-local-state =
    mkEvalCheck "domain-desktop-chrome-personal-profile-icon-activation-targets-local-state"
      iconActivationTargetsLocalState
      "the icon activation must target Local State, not Default/Preferences, because the profile avatar and highlight color live in profile.info_cache in Local State and a Default/Preferences merge would silently no-op";
}
