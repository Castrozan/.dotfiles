{ userBinPath }:
[
  {
    description = "Ctrl+Volume Up cycles smart-home light scene on chise via SSH";
    manipulators = [
      {
        type = "basic";
        from = {
          consumer_key_code = "volume_increment";
          modifiers.mandatory = [ "control" ];
        };
        to = [
          {
            shell_command = "${userBinPath}/ha-light-scene-cycle";
          }
        ];
      }
    ];
  }
  {
    description = "Ctrl+Volume Down toggles air conditioner on chise via SSH";
    manipulators = [
      {
        type = "basic";
        from = {
          consumer_key_code = "volume_decrement";
          modifiers.mandatory = [ "control" ];
        };
        to = [
          {
            shell_command = "${userBinPath}/ha-ac-toggle";
          }
        ];
      }
    ];
  }
  {
    description = "Ctrl+Mute turns off all smart-home lights on chise via SSH";
    manipulators = [
      {
        type = "basic";
        from = {
          consumer_key_code = "mute";
          modifiers.mandatory = [ "control" ];
        };
        to = [
          {
            shell_command = "${userBinPath}/ha-light off all";
          }
        ];
      }
    ];
  }
]
