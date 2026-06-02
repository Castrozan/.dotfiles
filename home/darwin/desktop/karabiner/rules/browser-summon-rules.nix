let
  hammerspoonCommandLineBinaryPath = "/opt/homebrew/bin/hs";

  makeSummonViaHammerspoonGlobalFunctionManipulator = letter: hammerspoonGlobalFunctionName: {
    type = "basic";
    from = {
      key_code = letter;
      modifiers.mandatory = [ "command" ];
    };
    to = [
      {
        shell_command = "${hammerspoonCommandLineBinaryPath} -c \"${hammerspoonGlobalFunctionName}()\"";
      }
    ];
  };
in
[
  {
    description = "Cmd+B summons Brave Browser to the current workspace via Hammerspoon";
    manipulators = [
      (makeSummonViaHammerspoonGlobalFunctionManipulator "b" "summonBraveBrowserToCurrentWorkspace")
    ];
  }
  {
    description = "Cmd+C summons Google Chrome to the current workspace via Hammerspoon";
    manipulators = [
      (makeSummonViaHammerspoonGlobalFunctionManipulator "c" "summonGoogleChromeToCurrentWorkspace")
    ];
  }
]
