{ userBinPath }:
let
  controlChordActiveVariableName = "smart_home_control_chord_active";

  controlKeyChordTrackingManipulator = controlKeyCode: {
    type = "basic";
    from = {
      key_code = controlKeyCode;
      modifiers.optional = [ "any" ];
    };
    to = [
      {
        set_variable = {
          name = controlChordActiveVariableName;
          value = 1;
        };
      }
      { key_code = controlKeyCode; }
    ];
    to_after_key_up = [
      {
        set_variable = {
          name = controlChordActiveVariableName;
          value = 0;
        };
      }
    ];
  };

  controlPlusConsumerKeyManipulator = consumerKeyCode: shellCommand: {
    type = "basic";
    from.consumer_key_code = consumerKeyCode;
    conditions = [
      {
        type = "variable_if";
        name = controlChordActiveVariableName;
        value = 1;
      }
    ];
    to = [ { shell_command = shellCommand; } ];
  };
in
[
  {
    description = "Track Control held so smart-home media-key chords can match (Apple consumer keys carry no modifier flags)";
    manipulators = [
      (controlKeyChordTrackingManipulator "left_control")
      (controlKeyChordTrackingManipulator "right_control")
    ];
  }
  {
    description = "Ctrl+Volume Up cycles smart-home light scene on chise via SSH";
    manipulators = [
      (controlPlusConsumerKeyManipulator "volume_increment" "${userBinPath}/ha-light-scene-cycle")
    ];
  }
  {
    description = "Ctrl+Volume Down toggles air conditioner on chise via SSH";
    manipulators = [
      (controlPlusConsumerKeyManipulator "volume_decrement" "${userBinPath}/ha-ac-toggle")
    ];
  }
  {
    description = "Ctrl+Mute turns off all smart-home lights on chise via SSH";
    manipulators = [
      (controlPlusConsumerKeyManipulator "mute" "${userBinPath}/ha-light off all")
    ];
  }
]
