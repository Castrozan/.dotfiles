# Description: Toggle Dell game shift mode
{ config, pkgs, ... }:

let
  gameShift = pkgs.writeShellApplication {
    name = "game-shift";
    runtimeInputs = [
      pkgs.coreutils
      pkgs.kmod
    ];
    text = builtins.readFile ./game-shift.sh;
  };

in
{
  # Enable the ACPI call module for dell g15 management with game-shift.sh
  boot.extraModulePackages = with config.boot.kernelPackages; [ acpi_call ];

  environment.systemPackages = [ gameShift ];
}
