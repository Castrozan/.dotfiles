{ userBinPath }:
[
  {
    description = "Cmd+B summons Brave Browser";
    manipulators = [
      {
        type = "basic";
        from = {
          key_code = "b";
          modifiers.mandatory = [ "command" ];
        };
        to = [
          {
            shell_command = "${userBinPath}/summon-brave";
          }
        ];
      }
    ];
  }
  {
    description = "Cmd+C summons Chrome";
    manipulators = [
      {
        type = "basic";
        from = {
          key_code = "c";
          modifiers.mandatory = [ "command" ];
        };
        to = [
          {
            shell_command = "${userBinPath}/summon-chrome";
          }
        ];
      }
    ];
  }
]
