{ conditions }:
let
  remapControlZoomKeyToCommandZoom = zoomKeyCode: mandatoryModifiers: {
    type = "basic";
    from = {
      key_code = zoomKeyCode;
      modifiers = {
        mandatory = mandatoryModifiers;
        optional = [ "caps_lock" ];
      };
    };
    to = [
      {
        key_code = zoomKeyCode;
        modifiers = [ "command" ];
      }
    ];
    inherit conditions;
  };
in
[
  (remapControlZoomKeyToCommandZoom "equal_sign" [
    "control"
    "shift"
  ])
  (remapControlZoomKeyToCommandZoom "equal_sign" [ "control" ])
  (remapControlZoomKeyToCommandZoom "hyphen" [
    "control"
    "shift"
  ])
  (remapControlZoomKeyToCommandZoom "hyphen" [ "control" ])
]
