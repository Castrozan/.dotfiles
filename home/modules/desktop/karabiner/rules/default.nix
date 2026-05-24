{ username }:
let
  terminalBundleIdentifiers = [
    "^com\\.github\\.wez\\.wezterm$"
    "^net\\.kovidgoyal\\.kitty$"
    "^com\\.apple\\.Terminal$"
    "^com\\.googlecode\\.iterm2$"
  ];

  excludeTerminalsCondition = [
    {
      type = "frontmost_application_unless";
      bundle_identifiers = terminalBundleIdentifiers;
    }
  ];

  onlyTerminalsCondition = [
    {
      type = "frontmost_application_if";
      bundle_identifiers = terminalBundleIdentifiers;
    }
  ];

  makeControlToCommandManipulator = fromLetter: toLetter: {
    type = "basic";
    from = {
      key_code = fromLetter;
      modifiers = {
        mandatory = [ "control" ];
        optional = [ "any" ];
      };
    };
    to = [
      {
        key_code = toLetter;
        modifiers = [ "command" ];
      }
    ];
    conditions = excludeTerminalsCondition;
  };

  controlToCommandLetters = [
    "a"
    "b"
    "c"
    "d"
    "e"
    "f"
    "g"
    "i"
    "j"
    "k"
    "l"
    "n"
    "o"
    "p"
    "q"
    "r"
    "s"
    "t"
    "u"
    "v"
    "x"
    "y"
    "z"
  ];

  userBinPath = "/etc/profiles/per-user/${username}/bin";
in
(import ./system-shortcuts-rules.nix)
++ (import ./window-management-rules.nix { inherit userBinPath; })
++ (import ./terminal-input-method-rules.nix { inherit onlyTerminalsCondition; })
++ (import ./function-key-passthrough-in-terminals-rules.nix { inherit onlyTerminalsCondition; })
++ (import ./word-navigation-rules.nix { inherit excludeTerminalsCondition; })
++ (import ./browser-summon-rules.nix { inherit userBinPath; })
++ (import ./brave-keybind-passthrough-rules.nix)
++ (import ./linux-style-modifier-rules.nix {
  inherit excludeTerminalsCondition makeControlToCommandManipulator controlToCommandLetters;
})
++ (import ./smart-home-control-rules.nix { inherit userBinPath; })
