{
  launchd.agents.maccy = {
    enable = true;
    config = {
      Label = "com.dotfiles.maccy";
      ProgramArguments = [
        "/Applications/Maccy.app/Contents/MacOS/Maccy"
        "-KeyboardShortcuts_popup"
        ''"{\"carbonKeyCode\":9,\"carbonModifiers\":768}"''
        "-pasteByDefault"
        "<true/>"
        "-SUEnableAutomaticChecks"
        "<false/>"
        "-loginItemEnabled"
        "<false/>"
      ];
      KeepAlive = true;
      RunAtLoad = true;
      StandardOutPath = "/tmp/maccy.log";
      StandardErrorPath = "/tmp/maccy.err.log";
    };
  };
}
