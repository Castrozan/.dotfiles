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

  braveCloseTabAcceleratorIncludesBothCmdWAndCtrlW =
    bravePreferencesOverrides.brave.accelerators."34015" == [
      "Command+KeyW"
      "Control+KeyW"
    ];

  braveSpellcheckIsLockedToEnGb = bravePreferencesOverrides.spellcheck.dictionaries == [ "en-GB" ];

  braveGoogleSigninIsDisabledInPreferencesOverrides =
    bravePreferencesOverrides.signin.allowed == false;
in
{
  domain-desktop-brave-duplicate-tab-bound-to-control-d =
    mkEvalCheck "domain-desktop-brave-duplicate-tab-bound-to-control-d"
      braveDuplicateTabCustomKeybindIsBoundToControlD
      "Brave Duplicate Tab (command id 34027) must be bound to Control+KeyD";

  domain-desktop-brave-close-tab-bound-to-both-cmd-w-and-ctrl-w =
    mkEvalCheck "domain-desktop-brave-close-tab-bound-to-both-cmd-w-and-ctrl-w"
      braveCloseTabAcceleratorIncludesBothCmdWAndCtrlW
      "Brave Close Tab (command id 34015) must keep its default Command+KeyW and add Control+KeyW";

  domain-desktop-brave-spellcheck-locked-to-en-gb =
    mkEvalCheck "domain-desktop-brave-spellcheck-locked-to-en-gb" braveSpellcheckIsLockedToEnGb
      "Brave spellcheck.dictionaries must contain exactly en-GB";

  domain-desktop-brave-google-signin-disabled-in-overrides =
    mkEvalCheck "domain-desktop-brave-google-signin-disabled-in-overrides"
      braveGoogleSigninIsDisabledInPreferencesOverrides
      "Brave signin.allowed must be false in preferences overrides";
}
