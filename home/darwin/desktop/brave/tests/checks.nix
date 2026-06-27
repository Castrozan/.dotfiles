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

  braveCloseTabAcceleratorIsBoundToCtrlWOnly =
    bravePreferencesOverrides.brave.accelerators."34015" == [
      "Control+KeyW"
    ];

  braveCloseWindowAcceleratorIsBoundToCmdW =
    bravePreferencesOverrides.brave.accelerators."34012" == [
      "Command+KeyW"
      "Command+Shift+KeyW"
    ];

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

  braveZoomInAcceleratorAddsControlShiftEqualAlongsideCommandEqual =
    bravePreferencesOverrides.brave.accelerators."38001" == [
      "Command+Equal"
      "Control+Shift+Equal"
    ];

  braveZoomOutAcceleratorAddsControlShiftMinusAlongsideCommandMinus =
    bravePreferencesOverrides.brave.accelerators."38003" == [
      "Command+Minus"
      "Control+Shift+Minus"
    ];
in
{
  domain-desktop-brave-duplicate-tab-bound-to-control-d =
    mkEvalCheck "domain-desktop-brave-duplicate-tab-bound-to-control-d"
      braveDuplicateTabCustomKeybindIsBoundToControlD
      "Brave Duplicate Tab (command id 34027) must be bound to Control+KeyD";

  domain-desktop-brave-close-tab-bound-to-ctrl-w-only =
    mkEvalCheck "domain-desktop-brave-close-tab-bound-to-ctrl-w-only"
      braveCloseTabAcceleratorIsBoundToCtrlWOnly
      "Brave Close Tab (command id 34015) must be bound to Control+KeyW only so Cmd+W is free for Close Window";

  domain-desktop-brave-close-window-bound-to-cmd-w =
    mkEvalCheck "domain-desktop-brave-close-window-bound-to-cmd-w"
      braveCloseWindowAcceleratorIsBoundToCmdW
      "Brave Close Window (command id 34012) must be bound to Command+KeyW and keep Command+Shift+KeyW";

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

  domain-desktop-brave-zoom-in-adds-control-shift-equal =
    mkEvalCheck "domain-desktop-brave-zoom-in-adds-control-shift-equal"
      braveZoomInAcceleratorAddsControlShiftEqualAlongsideCommandEqual
      "Brave Zoom In (command id 38001) must keep Command+Equal and add Control+Shift+Equal so Ctrl+Shift++ zooms in";

  domain-desktop-brave-zoom-out-adds-control-shift-minus =
    mkEvalCheck "domain-desktop-brave-zoom-out-adds-control-shift-minus"
      braveZoomOutAcceleratorAddsControlShiftMinusAlongsideCommandMinus
      "Brave Zoom Out (command id 38003) must keep Command+Minus and add Control+Shift+Minus so Ctrl+Shift+- zooms out";
}
