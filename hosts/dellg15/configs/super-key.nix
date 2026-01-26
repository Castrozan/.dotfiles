{
  pkgs,
  ...
}:
# GNOME-like Super key behavior using interception-tools + dual-function-keys
# Tap Super alone → sends F13 (bound to fuzzel in Hyprland)
# Hold Super + other key → normal modifier behavior
#
# This solves the fundamental problem: Hyprland's bindr fires on release
# regardless of what keys were pressed while the modifier was held.
# dual-function-keys intercepts at the input layer and only sends F13
# if Super was pressed and released without any other key.
{
  services.interception-tools = {
    enable = true;
    plugins = [ pkgs.interception-tools-plugins.dual-function-keys ];
    udevmonConfig = ''
      - JOB: "${pkgs.interception-tools}/bin/intercept -g $DEVNODE | ${pkgs.interception-tools-plugins.dual-function-keys}/bin/dual-function-keys -c /etc/interception/dual-function-keys.yaml | ${pkgs.interception-tools}/bin/uinput -d $DEVNODE"
        DEVICE:
          EVENTS:
            EV_KEY: [KEY_LEFTMETA, KEY_RIGHTMETA]
    '';
  };

  # dual-function-keys configuration
  # Using KEY_PROG1 (code 148) which is well-supported by Wayland/libinput
  environment.etc."interception/dual-function-keys.yaml".text = ''
    TIMING:
      TAP_MILLISEC: 200
      DOUBLE_TAP_MILLISEC: 0
      SYNTHETIC_KEYS_PAUSE_MILLISEC: 0

    MAPPINGS:
      - KEY: KEY_LEFTMETA
        TAP: KEY_PROG1
        HOLD: KEY_LEFTMETA
      - KEY: KEY_RIGHTMETA
        TAP: KEY_PROG1
        HOLD: KEY_RIGHTMETA
  '';
}
