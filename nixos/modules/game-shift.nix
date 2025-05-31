# Description: Toggle Dell game shift mode
{
  config,
  pkgs,
  ...
}:

let
  # Non-sudo version for status checking only
  game-shift-status = pkgs.writeShellScriptBin "game-shift-status" ''
    #!/usr/bin/env bash

    # Check if acpi_call module is loaded
    if ! lsmod | grep -q "acpi_call"; then
      echo "acpi_call module is not loaded. Use 'sudo modprobe acpi_call' first."
      exit 1
    fi

    # Try to read the current status (this may work without sudo in some cases)
    if [ -r /proc/acpi/call ]; then
      echo '\_SB.AMW3.WMAX 0 0x25 { 2, 0, 0, 0}' > /proc/acpi/call 2>/dev/null
      result=$(cat /proc/acpi/call 2>/dev/null | tr -d '\0')
      
      if [[ "$result" == "0x0" ]]; then
        echo "gmode is OFF"
      else
        echo "gmode is ON"
      fi
    else
      echo "Cannot read Game Shift status (permission denied)"
      echo "Use 'sudo game-shift' to toggle Game Shift mode"
    fi
  '';

  # Sudo version for actually toggling the mode
  game-shift = pkgs.writeShellScriptBin "game-shift" ''
    #!/usr/bin/env bash

    # Load the acpi_call module if not loaded
    if ! lsmod | grep -q "acpi_call"; then
      echo "Loading acpi_call module..."
      sudo modprobe acpi_call
    fi

    if [ "$EUID" -ne 0 ]; then
      # User is not root, use sudo
      echo "Game Shift requires root privileges. Running with sudo..."
      exec sudo $0 "$@"
      exit $?
    fi

    # We're root now, proceed with ACPI calls
    echo '\_SB.AMW3.WMAX 0 0x25 { 1, 0, 0, 0}' > /proc/acpi/call
    echo '\_SB.PCI0.LPC0.EC0._Q14' > /proc/acpi/call
    echo '\_SB.AMW3.WMAX 0 0x25 { 2, 0, 0, 0}' > /proc/acpi/call

    # Capture the output and remove any null bytes
    result=$(cat /proc/acpi/call | tr -d '\0')

    if [[ "$result" == "0x0" ]]; then
        echo "gmode is OFF"
    else
        echo "gmode is ON"
    fi
  '';

  # Add a polkit rule to allow users in the wheel group to run game-shift without password
  game-shift-polkit = pkgs.writeTextFile {
    name = "game-shift-polkit";
    destination = "/etc/polkit-1/rules.d/90-game-shift.rules";
    text = ''
      polkit.addRule(function(action, subject) {
        if (action.id == "org.freedesktop.policykit.exec" &&
            action.lookup("program") == "${game-shift}/bin/game-shift" &&
            subject.isInGroup("wheel")) {
          return polkit.Result.YES;
        }
      });
    '';
  };

in
{
  # Enable the ACPI call module for dell g15 management with game-shift.sh
  boot.extraModulePackages = with config.boot.kernelPackages; [ acpi_call ];

  # Load ACPI call at boot time
  boot.kernelModules = [ "acpi_call" ];

  # Make sure ACPI call is accessible
  boot.kernelParams = [ "acpi_call.allow_uid=1000" ];

  # System packages
  environment.systemPackages = [
    game-shift
    game-shift-status
  ];

  # Create udev rule to make /proc/acpi/call accessible to the group
  services.udev.extraRules = ''
    # Make acpi_call accessible to users in the wheel group
    KERNEL=="acpi_call", MODE="0664", GROUP="wheel"
  '';

  # Set up sudo rule for game-shift
  security.sudo.extraRules = [
    {
      users = [ "ALL" ];
      commands = [
        {
          command = "${game-shift}/bin/game-shift";
          options = [ "NOPASSWD" ];
        }
      ];
    }
  ];

  # Install the polkit rules
  environment.etc."polkit-1/rules.d/90-game-shift.rules".source = game-shift-polkit.outPath;
}
