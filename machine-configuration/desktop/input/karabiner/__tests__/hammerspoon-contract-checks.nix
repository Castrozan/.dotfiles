{
  allManipulators,
  applicationFocusVariableNames,
  helpers,
  inputs,
  lib,
}:
let
  inherit (helpers) mkEvalCheck;

  hammerspoonConfiguration = helpers.homeManagerTestConfigurationForDarwin [
    inputs.hammerspoon.homeManagerModules.default
  ];
  hammerspoonFiles = hammerspoonConfiguration.home.file;

  hammerspoonApplicationFocusModuleContent =
    builtins.readFile
      hammerspoonFiles.".hammerspoon/karabiner_application_focus_variables.lua".source;

  hammerspoonSetsEveryApplicationFocusVariable = lib.all (
    applicationFocusVariableName:
    lib.hasInfix applicationFocusVariableName hammerspoonApplicationFocusModuleContent
  ) applicationFocusVariableNames;

  browserSummonRules = import ../rules/browser-summon-rules.nix;

  hammerspoonInitModuleContent = builtins.readFile hammerspoonFiles.".hammerspoon/init.lua".source;

  commandETilingManipulators = lib.filter (
    manipulator:
    manipulator.from.key_code or "" == "e"
    && manipulator.from.modifiers.mandatory or [ ] == [ "command" ]
    && lib.any (toEntry: lib.hasInfix "toggleTwoWindowTiling()" (toEntry.shell_command or "")) (
      manipulator.to or [ ]
    )
  ) allManipulators;

  browserSummonShellCommands = lib.concatMap (
    rule:
    lib.concatMap (manipulator: map (toEntry: toEntry.shell_command or "") (manipulator.to or [ ])) (
      rule.manipulators or [ ]
    )
  ) browserSummonRules;

  hammerspoonFunctionNameInvokedByShellCommand =
    shellCommand:
    let
      match = builtins.match ''.*-c "([a-zA-Z0-9_]+)\(\)".*'' shellCommand;
    in
    if match == null then null else builtins.head match;

  browserSummonHammerspoonFunctionNames = lib.filter (name: name != null) (
    map hammerspoonFunctionNameInvokedByShellCommand browserSummonShellCommands
  );

  everyBrowserSummonFunctionIsDefinedInHammerspoonInit =
    browserSummonHammerspoonFunctionNames != [ ]
    && lib.all (
      functionName: lib.hasInfix "function ${functionName}(" hammerspoonInitModuleContent
    ) browserSummonHammerspoonFunctionNames;
in
{
  domain-desktop-karabiner-default-deny-variables-match-hammerspoon =
    mkEvalCheck "domain-desktop-karabiner-default-deny-variables-match-hammerspoon"
      hammerspoonSetsEveryApplicationFocusVariable
      "The hammerspoon karabiner_application_focus_variables module must set every application-focus variable name the karabiner default-deny guards read, otherwise a guard fails closed permanently and its rule silently stops working";

  domain-desktop-karabiner-browser-summon-functions-defined-in-hammerspoon =
    mkEvalCheck "domain-desktop-karabiner-browser-summon-functions-defined-in-hammerspoon"
      everyBrowserSummonFunctionIsDefinedInHammerspoonInit
      "Every hammerspoon global function the karabiner browser-summon rules invoke via `hs -c` must be defined in init.lua, otherwise renaming or dropping one side of the seam leaves Cmd+B or Cmd+C a silently dead keybind with all other tests still green";

  domain-desktop-karabiner-command-e-two-window-tiling-routes-to-hammerspoon =
    mkEvalCheck "domain-desktop-karabiner-command-e-two-window-tiling-routes-to-hammerspoon"
      (
        builtins.length commandETilingManipulators == 1
        && lib.hasInfix "function toggleTwoWindowTiling()" hammerspoonInitModuleContent
      )
      "Physical Cmd+E must invoke the Hammerspoon two-window tiling entry point exactly once, rather than a global Hammerspoon hotkey that would also consume Karabiner's existing Ctrl+E to Cmd+E remap";
}
