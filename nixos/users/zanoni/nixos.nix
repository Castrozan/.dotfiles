#
# NixOS Configuration for zanoni
#
{ pkgs, ... }:
let
  bashrc = builtins.readFile ../../../.bashrc;
in
{

  # Global Bash configuration
  # TODO: this is workaroun from home/programs/bash.nix
  environment.etc."bashrc".text = bashrc;

# Define a user account. Don't forget to set a password with ‘passwd’.
  users.users.zanoni = {
    isNormalUser = true;
    description = "zanoni";
    extraGroups = [ "networkmanager" "wheel" ];
    packages = with pkgs; [ ];
  };
}
