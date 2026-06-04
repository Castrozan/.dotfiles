let
  nonTerminalApplicationIsFrontmostVariableName = "non_terminal_application_is_frontmost";
in
{
  inherit nonTerminalApplicationIsFrontmostVariableName;

  defaultDenyCondition = {
    type = "variable_if";
    name = nonTerminalApplicationIsFrontmostVariableName;
    value = 1;
  };
}
