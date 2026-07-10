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

  bravePreferencesOverrides = builtins.fromJSON (builtins.readFile ../preferences-overrides.json);

  braveDuplicateTabCustomKeybindIsBoundToControlD =
    bravePreferencesOverrides.brave.accelerators."34027" == [ "Control+KeyD" ];

  braveDefaultSearchProviderIsPinnedToGooglePrepopulatedEngineGuid =
    bravePreferencesOverrides.default_search_provider.guid == "485bf7d3-0215-45af-87dc-538868000001";

  braveSpellcheckIsLockedToEnGb = bravePreferencesOverrides.spellcheck.dictionaries == [ "en-GB" ];

  braveGoogleSigninIsDisabledInPreferencesOverrides = !bravePreferencesOverrides.signin.allowed;

  braveFirstTabSelectionAcceleratorAddsAltDigitOneAlongsideCommandDefaults =
    bravePreferencesOverrides.brave.accelerators."34018" == [
      "Command+Digit1"
      "Command+Numpad1"
      "Alt+Digit1"
    ];

  braveLastTabSelectionAcceleratorAddsAltDigitNineAlongsideCommandDefaults =
    bravePreferencesOverrides.brave.accelerators."34026" == [
      "Command+Digit9"
      "Command+Numpad9"
      "Alt+Digit9"
    ];

  braveZoomAcceleratorsAreNotOverriddenBecauseBraveStripsControlShiftAdditionsOnLaunch =
    !(bravePreferencesOverrides.brave.accelerators ? "38001")
    && !(bravePreferencesOverrides.brave.accelerators ? "38003");
in
{
  domain-desktop-brave-duplicate-tab-bound-to-control-d =
    mkEvalCheck "domain-desktop-brave-duplicate-tab-bound-to-control-d"
      braveDuplicateTabCustomKeybindIsBoundToControlD
      "Brave Duplicate Tab (command id 34027) must be bound to Control+KeyD";

  domain-desktop-brave-default-search-provider-pinned-to-google =
    mkEvalCheck "domain-desktop-brave-default-search-provider-pinned-to-google"
      braveDefaultSearchProviderIsPinnedToGooglePrepopulatedEngineGuid
      "Brave default_search_provider.guid must be Google's prepopulated engine guid (prepopulate id 1)";

  domain-desktop-brave-spellcheck-locked-to-en-gb =
    mkEvalCheck "domain-desktop-brave-spellcheck-locked-to-en-gb" braveSpellcheckIsLockedToEnGb
      "Brave spellcheck.dictionaries must contain exactly en-GB";

  domain-desktop-brave-google-signin-disabled-in-overrides =
    mkEvalCheck "domain-desktop-brave-google-signin-disabled-in-overrides"
      braveGoogleSigninIsDisabledInPreferencesOverrides
      "Brave signin.allowed must be false in preferences overrides";

  domain-desktop-brave-first-tab-selection-adds-alt-digit-one =
    mkEvalCheck "domain-desktop-brave-first-tab-selection-adds-alt-digit-one"
      braveFirstTabSelectionAcceleratorAddsAltDigitOneAlongsideCommandDefaults
      "Brave Select Tab 0 (command id 34018) must keep Command+Digit1 and Command+Numpad1 and add Alt+Digit1";

  domain-desktop-brave-last-tab-selection-adds-alt-digit-nine =
    mkEvalCheck "domain-desktop-brave-last-tab-selection-adds-alt-digit-nine"
      braveLastTabSelectionAcceleratorAddsAltDigitNineAlongsideCommandDefaults
      "Brave Select Last Tab (command id 34026) must keep Command+Digit9 and Command+Numpad9 and add Alt+Digit9";

  domain-desktop-brave-zoom-accelerators-not-overridden =
    mkEvalCheck "domain-desktop-brave-zoom-accelerators-not-overridden"
      braveZoomAcceleratorsAreNotOverriddenBecauseBraveStripsControlShiftAdditionsOnLaunch
      "Brave Zoom In/Out (command ids 38001/38003) must not be set in preferences overrides because Brave strips Control+Shift+Equal / Control+Shift+Minus additions on launch; zoom is driven at the Karabiner keystroke layer instead (see brave-keybind-passthrough-rules)";
}
