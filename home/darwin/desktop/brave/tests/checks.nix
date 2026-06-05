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
}
