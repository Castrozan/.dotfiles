#
# NixOS Configuration for zanoni
#
{ pkgs, ... }:
let
  bashrc = builtins.readFile ../../../.bashrc;
in
{
  imports = [
    # TODO: Change this three to be managed as home programs
    ./packages.nix
    ./unstable-packages.nix
    ./scripts/default.nix
    ./virtualization.nix
    ./steam.nix
  ];

  programs.hyprland = {
    enable = true;
    xwayland.enable = true;
  };

  # Global Bash configuration
  # TODO: this is workaround from home/programs/bash.nix
  environment.etc."bashrc".text = bashrc;

  # Define a user account. Don't forget to set a password with ‘passwd’.
  users.users.zanoni = {
    isNormalUser = true;
    description = "zanoni";
    extraGroups = [
      "networkmanager"
      "wheel"
    ];
    packages = with pkgs; [ ];
  };
}
