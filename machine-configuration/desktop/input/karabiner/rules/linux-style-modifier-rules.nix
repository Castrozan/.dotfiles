{
  makeControlToCommandManipulator,
  controlToCommandLetters,
}:
[
  {
    description = "Linux-style Ctrl to Cmd shortcuts (except in terminals)";
    manipulators = map (letter: makeControlToCommandManipulator letter letter) controlToCommandLetters;
  }
]
