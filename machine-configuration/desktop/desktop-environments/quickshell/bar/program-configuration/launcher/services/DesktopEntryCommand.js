function quoteShellArgument(commandArgument) {
  return "'" + commandArgument.split("'").join("'\"'\"'") + "'";
}

function joinShellArguments(commandArguments) {
  return commandArguments
    .map((commandArgument) => quoteShellArgument(commandArgument))
    .join(" ");
}

function detachedLaunchCommand(desktopEntry) {
  let desktopEntryCommand =
    desktopEntry.command.length > 0
      ? joinShellArguments(desktopEntry.command)
      : desktopEntry.execString;

  if (desktopEntry.runInTerminal) {
    let terminalCommand = ["wezterm", "start"];

    if (desktopEntry.workingDirectory.length > 0) {
      terminalCommand.push("--cwd", desktopEntry.workingDirectory);
    }

    terminalCommand.push("--");

    if (desktopEntry.command.length > 0) {
      terminalCommand = terminalCommand.concat(desktopEntry.command);
    } else {
      terminalCommand.push("sh", "-lc", desktopEntry.execString);
    }

    return joinShellArguments(terminalCommand);
  }

  if (desktopEntry.workingDirectory.length > 0) {
    return `cd ${quoteShellArgument(desktopEntry.workingDirectory)} && ${desktopEntryCommand}`;
  }

  return desktopEntryCommand;
}
