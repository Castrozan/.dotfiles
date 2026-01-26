{ pkgs, ... }:
{
  home = {
    file.".config/hypr".source = ../../../.config/hypr;

    packages = with pkgs; [
      # Wayland tools
      wl-clipboard

      # Wallpaper
      hyprpaper
      swaybg

      # Notifications
      mako
      libnotify

      # Lock screen and idle
      hyprlock
      hypridle

      # Media & volume
      playerctl
      pamixer

      # OSD for volume/brightness
      swayosd

      # Emoji picker
      bemoji

      # Screenshot tools
      hyprshot
      grim
      slurp
      satty

      # Screen recording
      wf-recorder

      # Clipboard history
      cliphist

      # Color picker
      hyprpicker

      # JSON processing
      jq

      # Logout menu
      wlogout

      # Polkit agent
      polkit_gnome

      # Calculator
      gnome-calculator

      # Calendar popup helper
      yad

      # Bluetooth manager
      blueman

      # Audio control
      pavucontrol
    ];
  };
}
