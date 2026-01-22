{ pkgs, ... }:
{
  imports = [ ./omarchy-scripts.nix ];

  home.file.".config/hypr".source = ../../../.config/hypr;
  home.file.".config/waybar".source = ../../../.config/waybar;

  # Walker config - symlink individual files so walker can create its own files
  home.file.".config/walker/config.toml".source = ../../../.config/walker/config.toml;
  home.file.".config/walker/themes/omarchy-default.css".source =
    ../../../.config/walker/themes/omarchy-default.css;
  home.file.".config/walker/themes/omarchy-default.toml".source =
    ../../../.config/walker/themes/omarchy-default.toml;
  home.file.".config/walker/themes/omarchy-default.xml".source =
    ../../../.config/walker/themes/omarchy-default.xml;

  # Omarchy theme system - symlink read-only parts, let 'current' be runtime-writable
  home.file.".config/omarchy/themes".source = ../../../.config/omarchy/themes;
  home.file.".config/omarchy/themed".source = ../../../.config/omarchy/themed;

  # Initialize omarchy theme directory structure
  home.activation.initOmarchyTheme = ''
    mkdir -p $HOME/.config/omarchy/current/theme
    mkdir -p $HOME/.config/omarchy/user-themes
    mkdir -p $HOME/.config/omarchy/backgrounds
    touch $HOME/.config/omarchy/current/theme/hyprland.conf
  '';

  home.packages = with pkgs; [
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

    # Status bar
    waybar

    # OSD for volume/brightness (omarchy feature)
    swayosd

    # App launcher
    fuzzel
    walker

    # Emoji picker
    bemoji

    # YAML/JSON processing (for theme templates)
    yq-go

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
