# Description: Toggle Dell game shift mode
{ config, pkgs, ... }:

let
  game-shift = pkgs.writeShellScriptBin "game-shift" ''
    #!/usr/bin/env bash

    # Load the acpi_call module
    modprobe acpi_call

    echo '\_SB.AMW3.WMAX 0 0x25 { 1, 0, 0, 0}' | tee /proc/acpi/call
    echo '\_SB.PCI0.LPC0.EC0._Q14' | tee /proc/acpi/call
    echo '\_SB.AMW3.WMAX 0 0x25 { 2, 0, 0, 0}' | tee /proc/acpi/call
    
    # Capture the output and remove any null bytes
    result=$(cat /proc/acpi/call | tr -d '\0')

    if [[ "$result" == "0x0" ]]; then
        echo "gmode is OFF"
    else
        echo "gmode is ON"
    fi
  '';

in
{
  # Enable the ACPI call module for dell g15 management with game-shift.sh
  boot.extraModulePackages = with config.boot.kernelPackages; [ acpi_call ];

  environment.systemPackages = [ game-shift ];
}
