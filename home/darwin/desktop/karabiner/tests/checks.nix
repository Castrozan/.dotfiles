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

  applicationFocusDefaultDenyGuards = import ../rules/application-focus-default-deny-guards.nix;
  inherit (applicationFocusDefaultDenyGuards) applicationFocusVariableNames;

  allManipulators = lib.concatMap (rule: rule.manipulators or [ ]) karabinerRules;

  manipulatorHasFrontmostConditionMatching =
    frontmostConditionType: bundleIdentifierInfix: manipulator:
    lib.any (
      condition:
      condition.type or "" == frontmostConditionType
      && lib.any (bundleIdentifier: lib.hasInfix bundleIdentifierInfix (lib.toLower bundleIdentifier)) (
        condition.bundle_identifiers or [ ]
      )
    ) (manipulator.conditions or [ ]);

  manipulatorHasDefaultDenyGuard =
    guardVariableName: manipulator:
    lib.any (
      condition:
      condition.type or "" == "variable_if"
      && condition.name or "" == guardVariableName
      && (condition.value or null) == 1
    ) (manipulator.conditions or [ ]);

  everyManipulatorWithFrontmostConditionIsDefaultDenyGuarded =
    frontmostConditionType: bundleIdentifierInfix: guardVariableName:
    let
      matchingManipulators = lib.filter (manipulatorHasFrontmostConditionMatching frontmostConditionType bundleIdentifierInfix) allManipulators;
    in
    matchingManipulators != [ ]
    && lib.all (manipulatorHasDefaultDenyGuard guardVariableName) matchingManipulators;

  hammerspoonApplicationFocusModuleContent = builtins.readFile ../../hammerspoon/karabiner_application_focus_variables.lua;

  hammerspoonSetsEveryApplicationFocusVariable = lib.all (
    applicationFocusVariableName:
    lib.hasInfix applicationFocusVariableName hammerspoonApplicationFocusModuleContent
  ) applicationFocusDefaultDenyGuards.allApplicationFocusVariableNames;
in
{
  domain-desktop-karabiner-brave-ctrl-d-passthrough-pre-empts-linux-style-remap =
    mkEvalCheck "domain-desktop-karabiner-brave-ctrl-d-passthrough-pre-empts-linux-style-remap"
      (passthroughIndex != null && linuxStyleIndex != null && passthroughIndex < linuxStyleIndex)
      "Brave Ctrl+D passthrough rule must appear before the Linux-style Ctrl-to-Cmd remap so it pre-empts the conversion when Brave is frontmost";

  domain-desktop-karabiner-except-in-terminals-rules-are-default-deny-guarded =
    mkEvalCheck "domain-desktop-karabiner-except-in-terminals-rules-are-default-deny-guarded"
      (everyManipulatorWithFrontmostConditionIsDefaultDenyGuarded "frontmost_application_unless" "wezterm"
        applicationFocusVariableNames.nonTerminalApplicationIsFrontmost
      )
      "Every except-in-terminals manipulator must also carry the non_terminal_application_is_frontmost == 1 default-deny guard, so the Ctrl-to-Cmd remaps fail closed during karabiner's post-restart startup window instead of hijacking Ctrl+C and the tmux prefix in the terminal";

  domain-desktop-karabiner-only-in-terminals-rules-are-default-deny-guarded =
    mkEvalCheck "domain-desktop-karabiner-only-in-terminals-rules-are-default-deny-guarded"
      (everyManipulatorWithFrontmostConditionIsDefaultDenyGuarded "frontmost_application_if" "wezterm"
        applicationFocusVariableNames.terminalApplicationIsFrontmost
      )
      "Every only-in-terminals manipulator must also carry the terminal_application_is_frontmost == 1 default-deny guard, so it fails closed during karabiner's startup window and stays correct when frontmost_application conditions go stale during a shared-secret desync";

  domain-desktop-karabiner-brave-frontmost-rules-are-default-deny-guarded =
    mkEvalCheck "domain-desktop-karabiner-brave-frontmost-rules-are-default-deny-guarded"
      (everyManipulatorWithFrontmostConditionIsDefaultDenyGuarded "frontmost_application_if" "brave"
        applicationFocusVariableNames.braveBrowserIsFrontmost
      )
      "Every brave-frontmost manipulator must also carry the brave_browser_is_frontmost == 1 default-deny guard, so it fails closed during karabiner's startup window and stays correct when frontmost_application conditions go stale during a shared-secret desync";

  domain-desktop-karabiner-chrome-frontmost-rules-are-default-deny-guarded =
    mkEvalCheck "domain-desktop-karabiner-chrome-frontmost-rules-are-default-deny-guarded"
      (everyManipulatorWithFrontmostConditionIsDefaultDenyGuarded "frontmost_application_if" "chrome"
        applicationFocusVariableNames.chromeBrowserIsFrontmost
      )
      "Every chrome-frontmost manipulator must also carry the chrome_browser_is_frontmost == 1 default-deny guard, so it fails closed during karabiner's startup window and stays correct when frontmost_application conditions go stale during a shared-secret desync";

  domain-desktop-karabiner-default-deny-variables-match-hammerspoon =
    mkEvalCheck "domain-desktop-karabiner-default-deny-variables-match-hammerspoon"
      hammerspoonSetsEveryApplicationFocusVariable
      "The hammerspoon karabiner_application_focus_variables module must set every application-focus variable name the karabiner default-deny guards read, otherwise a guard fails closed permanently and its rule silently stops working";
}
