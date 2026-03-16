{
  xdg.configFile."hypr-host/monitors.conf".text = ''
    monitor = eDP-1, disable
    monitor = , highres, auto, 1
  '';

  xdg.configFile."hypr-host/input.conf".text = ''
    device {
        name = dell0a20:00-06cb:ce65-touchpad
        sensitivity = 0.0
    }
  '';
}
