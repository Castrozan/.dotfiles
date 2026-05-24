[
  {
    description = "Cmd+D to Show Desktop (Fn+F11)";
    manipulators = [
      {
        type = "basic";
        from = {
          key_code = "d";
          modifiers.mandatory = [ "command" ];
        };
        to = [
          {
            key_code = "f11";
            modifiers = [ "fn" ];
          }
        ];
      }
    ];
  }
  {
    description = "Print Screen to screenshot region to clipboard (Cmd+Shift+Ctrl+4)";
    manipulators = [
      {
        type = "basic";
        from.key_code = "print_screen";
        to = [
          {
            key_code = "4";
            modifiers = [
              "command"
              "shift"
              "control"
            ];
          }
        ];
      }
    ];
  }
]
