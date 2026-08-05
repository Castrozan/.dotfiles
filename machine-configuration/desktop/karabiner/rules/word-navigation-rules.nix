{ excludeTerminalsCondition }:
[
  {
    description = "Ctrl+Arrow to Option+Arrow for word jumping (except in terminals)";
    manipulators =
      map
        (arrowDirection: {
          type = "basic";
          from = {
            key_code = arrowDirection;
            modifiers = {
              mandatory = [ "control" ];
              optional = [ "shift" ];
            };
          };
          to = [
            {
              key_code = arrowDirection;
              modifiers = [ "option" ];
            }
          ];
          conditions = excludeTerminalsCondition;
        })
        [
          "left_arrow"
          "right_arrow"
        ];
  }
]
