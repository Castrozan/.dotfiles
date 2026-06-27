{ lib, karabinerRules }:
let
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

  isChromeControlShiftZoomRemapForKey =
    zoomKeyCode: manipulator:
    (manipulator.from.key_code or "") == zoomKeyCode
    && builtins.elem "control" (manipulator.from.modifiers.mandatory or [ ])
    && builtins.elem "shift" (manipulator.from.modifiers.mandatory or [ ])
    && lib.any (to: (to.key_code or "") == zoomKeyCode && (to.modifiers or [ ]) == [ "command" ]) (
      manipulator.to or [ ]
    )
    && lib.any (
      condition:
      condition.type or "" == "frontmost_application_if"
      && lib.any (b: lib.hasInfix "chrome" (lib.toLower b)) (condition.bundle_identifiers or [ ])
    ) (manipulator.conditions or [ ]);

  isPlainControlBDisableToVkNoneForBrowser =
    browserBundleInfix: manipulator:
    (manipulator.from.key_code or "") == "b"
    && (manipulator.from.modifiers.mandatory or [ ]) == [ "control" ]
    && !(builtins.elem "shift" (manipulator.from.modifiers.optional or [ ]))
    && !(builtins.elem "any" (manipulator.from.modifiers.optional or [ ]))
    && lib.any (to: (to.key_code or "") == "vk_none") (manipulator.to or [ ])
    && lib.any (
      condition:
      condition.type or "" == "frontmost_application_if"
      && lib.any (b: lib.hasInfix browserBundleInfix (lib.toLower b)) (
        condition.bundle_identifiers or [ ]
      )
    ) (manipulator.conditions or [ ]);

  bravePlainControlBDisableIndex = indexOfFirstRuleWhereManipulatorMatches (
    isPlainControlBDisableToVkNoneForBrowser "brave"
  );

  chromePlainControlBDisableIndex = indexOfFirstRuleWhereManipulatorMatches (
    isPlainControlBDisableToVkNoneForBrowser "chrome"
  );
in
{
  braveControlDPassthroughPreEmptsLinuxStyleRemap =
    passthroughIndex != null && linuxStyleIndex != null && passthroughIndex < linuxStyleIndex;

  chromeZoomInRemapIsPresent =
    indexOfFirstRuleWhereManipulatorMatches (isChromeControlShiftZoomRemapForKey "equal_sign") != null;

  chromeZoomOutRemapIsPresent =
    indexOfFirstRuleWhereManipulatorMatches (isChromeControlShiftZoomRemapForKey "hyphen") != null;

  bravePlainControlBDisablePreEmptsLinuxStyleRemap =
    bravePlainControlBDisableIndex != null
    && linuxStyleIndex != null
    && bravePlainControlBDisableIndex < linuxStyleIndex;

  chromePlainControlBDisablePreEmptsLinuxStyleRemap =
    chromePlainControlBDisableIndex != null
    && linuxStyleIndex != null
    && chromePlainControlBDisableIndex < linuxStyleIndex;
}
