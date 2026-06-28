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

  passthroughBravePlainControlKeyToPage = keyCode: {
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
        key_code = keyCode;
        modifiers = [ "control" ];
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
    description = "Brave: pass plain Ctrl+B through to the page as Ctrl+B (pre-empts the Linux-style Ctrl-to-Cmd remap so web apps can use it as a leader key) instead of remapping to Cmd+B (bold); Ctrl+Shift+B still reaches the bookmark bar toggle";
    manipulators = [
      (passthroughBravePlainControlKeyToPage "b")
    ];
  }
]
