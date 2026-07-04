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

  manipulatorMatchHelpers = import ./manipulator-match-helpers.nix { inherit lib karabinerRules; };
  inherit (manipulatorMatchHelpers)
    braveControlDPassthroughPreEmptsLinuxStyleRemap
    chromeZoomInRemapIsPresent
    chromeZoomOutRemapIsPresent
    bravePlainControlBPassthroughPreEmptsLinuxStyleRemap
    chromePlainControlBPassthroughPreEmptsLinuxStyleRemap
    braveCloseTabControlWRemapIsPresent
    braveCloseWindowCommandWRemapIsPresent
    chromeCloseTabControlWRemapIsPresent
    chromeCloseWindowCommandWRemapIsPresent
    ;

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
      braveControlDPassthroughPreEmptsLinuxStyleRemap
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

  domain-desktop-karabiner-chrome-zoom-in-control-shift-equal-remap-present =
    mkEvalCheck "domain-desktop-karabiner-chrome-zoom-in-control-shift-equal-remap-present"
      chromeZoomInRemapIsPresent
      "Chrome must remap Ctrl+Shift+= to Command+= so Ctrl+Shift++ zooms in, because Chrome ignores brave.accelerators and only a Karabiner rule can deliver the Mac zoom shortcut";

  domain-desktop-karabiner-chrome-zoom-out-control-shift-hyphen-remap-present =
    mkEvalCheck "domain-desktop-karabiner-chrome-zoom-out-control-shift-hyphen-remap-present"
      chromeZoomOutRemapIsPresent
      "Chrome must remap Ctrl+Shift+- to Command+- so Ctrl+Shift+- zooms out, because Chrome ignores brave.accelerators and only a Karabiner rule can deliver the Mac zoom shortcut";

  domain-desktop-karabiner-brave-ctrl-b-passthrough-pre-empts-linux-style-remap =
    mkEvalCheck "domain-desktop-karabiner-brave-ctrl-b-passthrough-pre-empts-linux-style-remap"
      bravePlainControlBPassthroughPreEmptsLinuxStyleRemap
      "Brave plain Ctrl+B must pass through to the page as Ctrl+B by a rule appearing before the Linux-style Ctrl-to-Cmd remap, so web apps can use Ctrl+B as a leader key instead of it being converted to Cmd+B (bold) when Brave is frontmost; Ctrl+Shift+B stays free for the bookmark bar toggle because the passthrough matches plain control only";

  domain-desktop-karabiner-chrome-ctrl-b-passthrough-pre-empts-linux-style-remap =
    mkEvalCheck "domain-desktop-karabiner-chrome-ctrl-b-passthrough-pre-empts-linux-style-remap"
      chromePlainControlBPassthroughPreEmptsLinuxStyleRemap
      "Chrome plain Ctrl+B must pass through to the page as Ctrl+B by a rule appearing before the Linux-style Ctrl-to-Cmd remap, so web apps can use Ctrl+B as a leader key instead of it being converted to Cmd+B (bold) when Chrome is frontmost; Ctrl+Shift+B stays free for the bookmark bar toggle because the passthrough matches plain control only";

  domain-desktop-karabiner-brave-close-tab-control-w-remap-present =
    mkEvalCheck "domain-desktop-karabiner-brave-close-tab-control-w-remap-present"
      braveCloseTabControlWRemapIsPresent
      "Brave must remap Ctrl+W to Command+W at the keystroke layer so Ctrl+W closes the tab via Brave's default Close Tab accelerator, because Brave reverts a brave.accelerators override that removes the Cmd+W default from Close Tab";

  domain-desktop-karabiner-brave-close-window-command-w-remap-present =
    mkEvalCheck "domain-desktop-karabiner-brave-close-window-command-w-remap-present"
      braveCloseWindowCommandWRemapIsPresent
      "Brave must remap Cmd+W to Command+Shift+W at the keystroke layer so Cmd+W closes the window via Brave's default Close Window accelerator, because Brave reverts the brave.accelerators override that binds Cmd+W to Close Window and restores Cmd+W to Close Tab on launch";

  domain-desktop-karabiner-chrome-close-tab-control-w-remap-present =
    mkEvalCheck "domain-desktop-karabiner-chrome-close-tab-control-w-remap-present"
      chromeCloseTabControlWRemapIsPresent
      "Chrome must remap Ctrl+W to Command+W at the keystroke layer so Ctrl+W closes the tab, because Chrome ignores brave.accelerators and only a Karabiner rule can deliver the Linux-style close-tab shortcut";

  domain-desktop-karabiner-chrome-close-window-command-w-remap-present =
    mkEvalCheck "domain-desktop-karabiner-chrome-close-window-command-w-remap-present"
      chromeCloseWindowCommandWRemapIsPresent
      "Chrome must remap Cmd+W to Command+Shift+W at the keystroke layer so Cmd+W closes the window, because Chrome ignores brave.accelerators and only a Karabiner rule can deliver the close-window shortcut";
}
