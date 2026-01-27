# Shared Hyprland modules - does NOT include Hyprland binary
# Import via nixos.nix or standalone.nix instead
{
  imports = [
    ./packages.nix
    ./calendar.nix
    ./cursor.nix
    ./omarchy.nix
    ./waybar.nix
    ./hyprshell.nix
    ./wlogout.nix
    ./swayosd.nix
    ./waybar-service.nix
    ./hypridle-service.nix
    ./swaync-service.nix
    ../fuzzel.nix
  ];
}
