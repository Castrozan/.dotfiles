{ pkgs, ... }:
{
  home.file.".config/hypr".source = ../../../.config/hypr;
  home.file.".config/waybar".source = ../../../.config/waybar;

  home.packages = with pkgs; [
    # Wayland tools
    wl-clipboard

    # Wallpaper
    hyprpaper

    # Notifications
    mako
    libnotify

    # Lock screen and idle
    hyprlock
    hypridle

    # Media & volume
    playerctl
    pamixer

    # Status bar
    waybar

    # OSD for volume/brightness (omarchy feature)
    swayosd

    # App launcher
    fuzzel

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

    # JSON processing (for hyprctl scripts)
    jq

    # Logout menu
    wlogout

    # Polkit agent
    polkit_gnome

    # Calculator
    gnome-calculator

    # Bluetooth manager
    blueman

    # Audio control
    pavucontrol
  ];
}
