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
  boot.extraModulePackages = with config.boot.kernelPackages; [ acpi_call ];

  environment.systemPackages = [ gameShift ];
}
