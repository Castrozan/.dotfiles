{ lib, ... }:

with lib.hm.gvariant;
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

    # "org/gnome/desktop/screensaver" = {
    #   picture-uri = "file:///home/gvolpe/Pictures/nixos.png";
    # };
  };

}
