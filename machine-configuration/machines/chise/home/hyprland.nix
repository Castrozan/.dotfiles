{
  xdg.configFile."hypr-host/monitors.conf".text = ''
    monitor = eDP-1, disable
    monitor = , highres, auto, 1
  '';

  xdg.configFile."hypr-host/input.conf".text = ''
    input {
      sensitivity = -0.9
    }

    device {
      name = dell0a6e:00-04f3:317e-touchpad
      sensitivity = -0.59292234
    }
  '';
}
