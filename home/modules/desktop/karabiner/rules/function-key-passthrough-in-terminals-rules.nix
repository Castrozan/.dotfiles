{ onlyTerminalsCondition }:
[
  {
    description = "F11 sends F11 (not volume down) inside terminals";
    manipulators = [
      {
        type = "basic";
        from.consumer_key_code = "volume_decrement";
        to = [ { key_code = "f11"; } ];
        conditions = onlyTerminalsCondition;
      }
    ];
  }
  {
    description = "F12 sends F12 (not volume up) inside terminals";
    manipulators = [
      {
        type = "basic";
        from.consumer_key_code = "volume_increment";
        to = [ { key_code = "f12"; } ];
        conditions = onlyTerminalsCondition;
      }
    ];
  }
]
