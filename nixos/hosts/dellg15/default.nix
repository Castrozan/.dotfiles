{ config, pkgs, ... }:

{
  imports =
    [
      ./configs/configuration.nix

      # NixOS modules
      # These are configurations that can be done on the system level
      ../../modules/system.nix
      # ../../modules/i3.nix

      # Include the results of the hardware scan.
      # Gen with the command: sudo nixos-generate-config --show-hardware-config
      ./configs/hardware-configuration.nix
    ];
}


