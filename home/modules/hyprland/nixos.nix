# Hyprland for NixOS systems
# Uses flake input directly - NixOS provides GPU drivers
{
  imports = [
    ./default.nix
    ./hyprland-nixos.nix
  ];
}
