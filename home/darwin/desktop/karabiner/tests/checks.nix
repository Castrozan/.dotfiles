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

  karabinerRules = import ../rules { username = "test"; };

  indexOfFirstRuleWhereManipulatorMatches =
    manipulatorPredicate:
    let
      ruleHasMatchingManipulator = rule: lib.any manipulatorPredicate (rule.manipulators or [ ]);
      allIndices = lib.lists.imap0 (indexInList: rule: {
        inherit indexInList;
        matches = ruleHasMatchingManipulator rule;
      }) karabinerRules;
      matchingEntries = builtins.filter (entry: entry.matches) allIndices;
    in
    if matchingEntries == [ ] then null else (builtins.head matchingEntries).indexInList;

  isBravePassthroughManipulatorForLetterD =
    manipulator:
    (manipulator.from.key_code or "") == "d"
    && builtins.elem "control" (manipulator.from.modifiers.mandatory or [ ])
    && lib.any (to: to.key_code or "" == "d" && to.modifiers or [ ] == [ "control" ]) (
      manipulator.to or [ ]
    )
    && lib.any (
      condition:
      condition.type or "" == "frontmost_application_if"
      && lib.any (b: lib.hasInfix "brave" (lib.toLower b)) (condition.bundle_identifiers or [ ])
    ) (manipulator.conditions or [ ]);

  isLinuxStyleControlToCommandRemapForLetterD =
    manipulator:
    (manipulator.from.key_code or "") == "d"
    && builtins.elem "control" (manipulator.from.modifiers.mandatory or [ ])
    && lib.any (to: builtins.elem "command" (to.modifiers or [ ])) (manipulator.to or [ ]);

  passthroughIndex = indexOfFirstRuleWhereManipulatorMatches isBravePassthroughManipulatorForLetterD;
  linuxStyleIndex = indexOfFirstRuleWhereManipulatorMatches isLinuxStyleControlToCommandRemapForLetterD;
in
{
  domain-desktop-karabiner-brave-ctrl-d-passthrough-pre-empts-linux-style-remap =
    mkEvalCheck "domain-desktop-karabiner-brave-ctrl-d-passthrough-pre-empts-linux-style-remap"
      (passthroughIndex != null && linuxStyleIndex != null && passthroughIndex < linuxStyleIndex)
      "Brave Ctrl+D passthrough rule must appear before the Linux-style Ctrl-to-Cmd remap so it pre-empts the conversion when Brave is frontmost";
}
