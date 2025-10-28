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
    
    # Lock screen
    hyprlock
    
    # Media & volume
    playerctl
    pamixer
    
    # Status bar
    waybar
  ];
}
