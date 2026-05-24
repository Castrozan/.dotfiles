{ userBinPath }:
[
  {
    description = "Cmd+W closes focused window via AeroSpace";
    manipulators = [
      {
        type = "basic";
        from = {
          key_code = "w";
          modifiers.mandatory = [ "command" ];
        };
        to = [
          {
            shell_command = "${userBinPath}/aerospace close";
          }
        ];
      }
    ];
  }
  {
    description = "Cmd+Q sends show to application-launcher daemon (send_user_command, no fork+exec)";
    manipulators = [
      {
        type = "basic";
        from = {
          key_code = "q";
          modifiers.mandatory = [ "command" ];
        };
        to = [
          {
            send_user_command = {
              endpoint = "/tmp/application-launcher.sock";
              payload = "show";
            };
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
