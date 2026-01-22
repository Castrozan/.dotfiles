{ pkgs, ... }:
{
  imports = [ ./omarchy-scripts.nix ];

  home = {
    file = {
      ".config/hypr".source = ../../../.config/hypr;
      ".config/waybar".source = ../../../.config/waybar;

      # Walker config - symlink individual files so walker can create its own files
      ".config/walker/config.toml".source = ../../../.config/walker/config.toml;
      ".config/walker/themes/omarchy-default.css".source =
        ../../../.config/walker/themes/omarchy-default.css;
      ".config/walker/themes/omarchy-default.toml".source =
        ../../../.config/walker/themes/omarchy-default.toml;
      ".config/walker/themes/omarchy-default.xml".source =
        ../../../.config/walker/themes/omarchy-default.xml;

      # Omarchy theme system - symlink read-only parts, let 'current' be runtime-writable
      ".config/omarchy/themes".source = ../../../.config/omarchy/themes;
      ".config/omarchy/themed".source = ../../../.config/omarchy/themed;
    };

    # Initialize omarchy theme directory structure
    activation.initOmarchyTheme = ''
      mkdir -p $HOME/.config/omarchy/current/theme
      mkdir -p $HOME/.config/omarchy/user-themes
      mkdir -p $HOME/.config/omarchy/backgrounds
      touch $HOME/.config/omarchy/current/theme/hyprland.conf
    '';

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
  };
}
