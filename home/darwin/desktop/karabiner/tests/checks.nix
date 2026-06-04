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

  nonTerminalFrontmostDefaultDenyGuard = import ../rules/non-terminal-frontmost-default-deny-guard.nix;

  allManipulators = lib.concatMap (rule: rule.manipulators or [ ]) karabinerRules;

  manipulatorExcludesTerminals =
    manipulator:
    lib.any (
      condition:
      condition.type or "" == "frontmost_application_unless"
      && lib.any (bundleIdentifier: lib.hasInfix "wezterm" (lib.toLower bundleIdentifier)) (
        condition.bundle_identifiers or [ ]
      )
    ) (manipulator.conditions or [ ]);

  manipulatorHasDefaultDenyGuard =
    manipulator:
    lib.any (
      condition:
      condition.type or "" == "variable_if"
      &&
        condition.name or ""
        == nonTerminalFrontmostDefaultDenyGuard.nonTerminalApplicationIsFrontmostVariableName
      && (condition.value or null) == 1
    ) (manipulator.conditions or [ ]);

  atLeastOneExcludeTerminalsManipulatorExists = lib.any manipulatorExcludesTerminals allManipulators;

  everyExcludeTerminalsManipulatorIsDefaultDenyGuarded = lib.all (
    manipulator:
    !(manipulatorExcludesTerminals manipulator) || manipulatorHasDefaultDenyGuard manipulator
  ) allManipulators;

  hammerspoonTerminalFocusVariableModuleContent = builtins.readFile ../../hammerspoon/karabiner_terminal_focus_variable.lua;

  hammerspoonReferencesGuardVariableName = lib.hasInfix nonTerminalFrontmostDefaultDenyGuard.nonTerminalApplicationIsFrontmostVariableName hammerspoonTerminalFocusVariableModuleContent;
in
{
  domain-desktop-karabiner-brave-ctrl-d-passthrough-pre-empts-linux-style-remap =
    mkEvalCheck "domain-desktop-karabiner-brave-ctrl-d-passthrough-pre-empts-linux-style-remap"
      (passthroughIndex != null && linuxStyleIndex != null && passthroughIndex < linuxStyleIndex)
      "Brave Ctrl+D passthrough rule must appear before the Linux-style Ctrl-to-Cmd remap so it pre-empts the conversion when Brave is frontmost";

  domain-desktop-karabiner-except-in-terminals-rules-are-default-deny-guarded =
    mkEvalCheck "domain-desktop-karabiner-except-in-terminals-rules-are-default-deny-guarded"
      (
        atLeastOneExcludeTerminalsManipulatorExists && everyExcludeTerminalsManipulatorIsDefaultDenyGuarded
      )
      "Every except-in-terminals manipulator must also carry the non_terminal_application_is_frontmost == 1 default-deny guard, so the Ctrl-to-Cmd remaps fail closed during karabiner's post-restart startup window instead of hijacking Ctrl+C and the tmux prefix in the terminal";

  domain-desktop-karabiner-default-deny-variable-name-matches-hammerspoon =
    mkEvalCheck "domain-desktop-karabiner-default-deny-variable-name-matches-hammerspoon"
      hammerspoonReferencesGuardVariableName
      "The hammerspoon karabiner_terminal_focus_variable module must set the same variable name the karabiner default-deny guard reads, otherwise the guard fails closed permanently and the Ctrl-to-Cmd remaps silently stop working";
}
