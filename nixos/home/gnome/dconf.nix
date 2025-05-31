{ ... }:
{
  # GNOME settings
  dconf.settings = {
    "org/gnome/desktop/peripherals/mouse" = {
      natural-scroll = false;
      speed = -0.5;
    };

    "org/gnome/desktop/interface" = {
      gtk-theme = "Adwaita-dark";
      color-scheme = "prefer-dark";
      cursor-theme = "Adwaita";
      cursor-size = 24;
      show-battery-percentage = true;
    };

    # "org/gnome/desktop/peripherals/touchpad" = {
    #   tap-to-click = false;
    #   two-finger-scrolling-enabled = true;
    # };

    # "org/gnome/desktop/input-sources" = {
    #   current = mkUint32 0;
    #   sources = [ (mkTuple [ "xkb" "us" ]) ];
    #   xkb-options = [ "terminate:ctrl_alt_bksp" "lv3:ralt_switch" "caps:ctrl_modifier" ];
    # };

    "org/gnome/desktop/background" = {
      color-shading-type = "solid";
      picture-options = "zoom";
      picture-uri = "file:///home/zanoni/.dotfiles/resources/alter-jellyfish-dark.jpg";
      picture-uri-dark = "file:///home/zanoni/.dotfiles/resources/alter-jellyfish-dark.jpg";
      primary-color = "#000000000000";
      secondary-color = "#000000000000";
    };

    "org/gnome/desktop/screensaver" = {
      picture-uri = "file:///home/zanoni/.dotfiles/resources/alter-jellyfish-dark.jpg";
    };

    "org/gnome/shell" = {
      enabled-extensions = [
        "default-workspace@mateusrodcosta.com"
        "wsmatrix@martin.zurowietz.de"
      ];
    };

    "org/gnome/shell/extensions/default-workspace" = {
      default-workspace-number = 3;
    };

    "org/gnome/shell/extensions/wsmatrix" = {
      num-columns = 5;
      num-rows = 2;
      show-popup = false;
    };

    # Custom keybindings
    "org/gnome/settings-daemon/plugins/media-keys" = {
      custom-keybindings = [
        "/org/gnome/settings-daemon/plugins/media-keys/custom-keybindings/custom0/"
      ];
    };

    "org/gnome/settings-daemon/plugins/media-keys/custom-keybindings/custom0" = {
      binding = "<Alt>a";
      command = "nix run github:quoteme/whisper-input";
      name = "whisper";
    };

    # Window manager keybindings
    "org/gnome/desktop/wm/keybindings" = {
      close = [ "<Shift><Control>w" ];
      switch-applications = [ ];
      switch-applications-backward = [ ];
      switch-windows = [ "<Alt>Tab" ];
      switch-windows-backward = [ "<Shift><Alt>Tab" ];
    };
  };
}
