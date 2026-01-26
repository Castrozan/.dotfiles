# Hyprland for non-NixOS systems (Ubuntu, Fedora, etc.)
# Uses nixGL wrapper to access host OpenGL libraries
{
  imports = [
    ./default.nix
    ./hyprland-nixgl.nix
  ];
}
