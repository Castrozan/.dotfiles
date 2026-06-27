let
  applicationFocusDefaultDenyGuards = import ./application-focus-default-deny-guards.nix;

  braveBundleIdentifierRegex = "^com\\.brave\\.Browser$";

  braveIsFrontmostConditions = [
    {
      type = "frontmost_application_if";
      bundle_identifiers = [ braveBundleIdentifierRegex ];
    }
    (applicationFocusDefaultDenyGuards.makeApplicationFocusDefaultDenyCondition applicationFocusDefaultDenyGuards.applicationFocusVariableNames.braveBrowserIsFrontmost)
  ];

  carveOutBraveFromControlToCommandRemapForLetter = letter: {
    type = "basic";
    from = {
      key_code = letter;
      modifiers = {
        mandatory = [ "control" ];
        optional = [ "any" ];
      };
    };
    to = [
      {
        key_code = letter;
        modifiers = [ "control" ];
      }
    ];
    conditions = braveIsFrontmostConditions;
  };

  remapBraveControlKeyToCommandShortcut = fromKeyCode: toKeyCode: toModifiers: {
    type = "basic";
    from = {
      key_code = fromKeyCode;
      modifiers = {
        mandatory = [ "control" ];
        optional = [ "any" ];
      };
    };
    to = [
      {
        key_code = toKeyCode;
        modifiers = toModifiers;
      }
    ];
    conditions = braveIsFrontmostConditions;
  };

  disableBravePlainControlKeyByMappingToVkNone = keyCode: {
    type = "basic";
    from = {
      key_code = keyCode;
      modifiers = {
        mandatory = [ "control" ];
        optional = [ ];
      };
    };
    to = [
      {
        key_code = "vk_none";
      }
    ];
    conditions = braveIsFrontmostConditions;
  };

  bravePassthroughLetters = [ "d" ];
in
[
  {
    description = "Brave: preserve Ctrl+letter passthrough so Brave's own accelerator table handles it (overrides Linux-style Ctrl-to-Cmd remap)";
    manipulators = map carveOutBraveFromControlToCommandRemapForLetter bravePassthroughLetters;
  }
  {
    description = "Brave: Linux-style Ctrl+H opens history and Ctrl+J opens downloads via the Mac Chromium shortcuts";
    manipulators = [
      (remapBraveControlKeyToCommandShortcut "h" "y" [ "command" ])
      (remapBraveControlKeyToCommandShortcut "j" "j" [
        "command"
        "shift"
      ])
    ];
  }
  {
    description = "Brave: disable plain Ctrl+B so it does nothing instead of being remapped to Cmd+B (bold); Ctrl+Shift+B still reaches the bookmark bar toggle";
    manipulators = [
      (disableBravePlainControlKeyByMappingToVkNone "b")
    ];
  }
]
