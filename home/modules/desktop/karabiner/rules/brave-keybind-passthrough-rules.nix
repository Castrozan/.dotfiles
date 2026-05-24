let
  braveBundleIdentifierRegex = "^com\\.brave\\.Browser$";

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
    conditions = [
      {
        type = "frontmost_application_if";
        bundle_identifiers = [ braveBundleIdentifierRegex ];
      }
    ];
  };

  bravePassthroughLetters = [ "d" ];
in
[
  {
    description = "Brave: preserve Ctrl+letter passthrough so Brave's own accelerator table handles it (overrides Linux-style Ctrl-to-Cmd remap)";
    manipulators = map carveOutBraveFromControlToCommandRemapForLetter bravePassthroughLetters;
  }
]
