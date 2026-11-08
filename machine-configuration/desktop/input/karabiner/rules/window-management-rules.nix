_:
let
  hammerspoonCommandLineBinaryPath = "/opt/homebrew/bin/hs";
  vicinaeToggleChord = import ../../../applications/launcher/vicinae-toggle-chord.nix;
in
[
  {
    description = "Cmd+Q toggles Vicinae through its global shortcut (no fork+exec)";
    manipulators = [
      {
        type = "basic";
        from = {
          key_code = "q";
          modifiers.mandatory = [ "command" ];
        };
        to = [ vicinaeToggleChord.karabinerOutput ];
      }
    ];
  }
  {
    description = "Cmd+E toggles the current and previous workspace windows side by side via Hammerspoon";
    manipulators = [
      {
        type = "basic";
        from = {
          key_code = "e";
          modifiers.mandatory = [ "command" ];
        };
        to = [
          {
            shell_command = "${hammerspoonCommandLineBinaryPath} -c \"toggleTwoWindowTiling()\"";
          }
        ];
      }
    ];
  }
  {
    description = "Cmd+Tab/Cmd+Shift+Tab workspace window switcher via daemon (send_user_command, no fork+exec)";
    manipulators = [
      {
        type = "basic";
        from = {
          key_code = "tab";
          modifiers.mandatory = [
            "command"
            "shift"
          ];
        };
        to = [
          {
            send_user_command = {
              endpoint = "/tmp/workspace-switcher.sock";
              payload = "prev";
            };
          }
        ];
      }
      {
        type = "basic";
        from = {
          key_code = "tab";
          modifiers.mandatory = [ "command" ];
        };
        to = [
          {
            send_user_command = {
              endpoint = "/tmp/workspace-switcher.sock";
              payload = "next";
            };
          }
        ];
      }
    ];
  }
  {
    description = "Cmd release commits workspace window switcher (daemon no-ops if inactive)";
    manipulators =
      map
        (commandKey: {
          type = "basic";
          from.key_code = commandKey;
          to = [ { key_code = commandKey; } ];
          to_after_key_up = [
            {
              send_user_command = {
                endpoint = "/tmp/workspace-switcher.sock";
                payload = "commit";
              };
            }
          ];
        })
        [
          "left_command"
          "right_command"
        ];
  }
]
