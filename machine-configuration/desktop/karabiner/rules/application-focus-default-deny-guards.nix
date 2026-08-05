let
  makeApplicationFocusDefaultDenyCondition = applicationFocusVariableName: {
    type = "variable_if";
    name = applicationFocusVariableName;
    value = 1;
  };

  applicationFocusVariableNames = {
    terminalApplicationIsFrontmost = "terminal_application_is_frontmost";
    nonTerminalApplicationIsFrontmost = "non_terminal_application_is_frontmost";
    braveBrowserIsFrontmost = "brave_browser_is_frontmost";
    chromeBrowserIsFrontmost = "chrome_browser_is_frontmost";
  };
in
{
  inherit makeApplicationFocusDefaultDenyCondition applicationFocusVariableNames;

  allApplicationFocusVariableNames = builtins.attrValues applicationFocusVariableNames;
}
