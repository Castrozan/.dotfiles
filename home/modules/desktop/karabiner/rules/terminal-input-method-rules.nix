{ onlyTerminalsCondition }:
[
  {
    description = "Ctrl+Space to Ctrl+Shift+Backslash in terminals (bypasses macOS input method interception)";
    manipulators = [
      {
        type = "basic";
        from = {
          key_code = "spacebar";
          modifiers.mandatory = [ "control" ];
        };
        to = [
          {
            key_code = "backslash";
            modifiers = [
              "control"
              "shift"
            ];
          }
        ];
        conditions = onlyTerminalsCondition;
      }
    ];
  }
]
