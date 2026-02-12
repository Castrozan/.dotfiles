{
  xdg.configFile."hypr-host/monitors.conf".text = ''
    monitor = HDMI-A-1, 1920x1080@120, auto, 1
    monitor = eDP-1, disable
  '';

  xdg.configFile."hypr-host/input.conf".text = ''
    device {
        name = dell0a20:00-06cb:ce65-touchpad
        sensitivity = 0.0
    }
  '';
}
