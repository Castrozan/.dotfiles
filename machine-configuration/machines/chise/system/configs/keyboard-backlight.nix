{ pkgs, ... }:
let
  pythonWithPyusb = pkgs.python3.withPackages (ps: [ ps.pyusb ]);
  keyboardBacklightScripts = pkgs.runCommand "keyboard-backlight-scripts" { } ''
    mkdir -p "$out"
    cp ${../scripts/keyboard-backlight}/*.py "$out/"
    substituteInPlace "$out/alienware_led_controller.py" \
      --replace-fail '@modprobe@' '${pkgs.kmod}/bin/modprobe' \
      --replace-fail '@rmmod@' '${pkgs.kmod}/bin/rmmod'
  '';

  setKeyboardBacklightBrightnessScript = pkgs.writeShellScript "set-keyboard-backlight-brightness" ''
    exec ${pythonWithPyusb}/bin/python3 ${keyboardBacklightScripts}/set_keyboard_brightness.py "$@"
  '';

  setKeyboardBacklightColorScript = pkgs.writeShellScript "set-keyboard-backlight-color" ''
    exec ${pythonWithPyusb}/bin/python3 ${keyboardBacklightScripts}/set_keyboard_color.py "$@"
  '';

  resetKeyboardBacklightScript = pkgs.writeShellScript "reset-keyboard-backlight" ''
    exec ${pythonWithPyusb}/bin/python3 ${keyboardBacklightScripts}/reset_keyboard_backlight.py "$@"
  '';

in
{
  environment.systemPackages = [
    (pkgs.writeShellScriptBin "set-keyboard-backlight-brightness" ''
      exec sudo ${setKeyboardBacklightBrightnessScript} "$@"
    '')
    (pkgs.writeShellScriptBin "set-keyboard-backlight-color" ''
      exec sudo ${setKeyboardBacklightColorScript} "$@"
    '')
    (pkgs.writeShellScriptBin "reset-keyboard-backlight" ''
      exec sudo ${resetKeyboardBacklightScript} "$@"
    '')
  ];

  systemd.services.dim-keyboard-backlight = {
    description = "Dim Dell G15 keyboard backlight to 5% on boot";
    wantedBy = [ "multi-user.target" ];
    after = [ "systemd-udevd.service" ];
    serviceConfig = {
      Type = "oneshot";
      ExecStart = "${setKeyboardBacklightBrightnessScript} 5";
      RemainAfterExit = true;
    };
  };
}
