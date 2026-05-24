{
  excludeTerminalsCondition,
  makeControlToCommandManipulator,
  controlToCommandLetters,
}:
[
  {
    description = "Ctrl+Click to Cmd+Click (except in terminals)";
    manipulators = [
      {
        type = "basic";
        from = {
          pointing_button = "button1";
          modifiers = {
            mandatory = [ "control" ];
            optional = [ "any" ];
          };
        };
        to = [
          {
            pointing_button = "button1";
            modifiers = [ "command" ];
          }
        ];
        conditions = excludeTerminalsCondition;
      }
    ];
  }
  {
    description = "Linux-style Ctrl to Cmd shortcuts (except in terminals)";
    manipulators = map (letter: makeControlToCommandManipulator letter letter) controlToCommandLetters;
  }
]
