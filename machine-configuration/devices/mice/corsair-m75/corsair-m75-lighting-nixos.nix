{
  lib,
  pkgs,
  inputs,
  utils,
  ...
}:
let
  openrgb = inputs.nixpkgs-openrgb.legacyPackages.${pkgs.stdenv.hostPlatform.system}.openrgb;
  slipstreamReceiverAlias = "/sys/subsystem/usb/devices/corsair-slipstream-receiver";
  slipstreamReceiverDeviceUnit = "${utils.escapeSystemdPath slipstreamReceiverAlias}.device";
in
{
  services.udev.extraRules = ''
    SUBSYSTEM=="usb", ENV{DEVTYPE}=="usb_device", ATTR{idVendor}=="1b1c", ATTR{idProduct}=="1bdc", TAG+="systemd", ENV{SYSTEMD_ALIAS}+="${slipstreamReceiverAlias}"
  '';

  systemd.services.corsair-m75-lighting-off = {
    description = "Hold the Corsair M75 Wireless mouse lighting off";
    wantedBy = [ slipstreamReceiverDeviceUnit ];
    bindsTo = [ slipstreamReceiverDeviceUnit ];
    after = [ slipstreamReceiverDeviceUnit ];
    startLimitIntervalSec = 0;
    environment.HOME = "/var/lib/corsair-m75-lighting-off";
    serviceConfig = {
      ExecStart = utils.escapeSystemdExecArgs [
        (lib.getExe openrgb)
        "--noautoconnect"
        "--server"
        "--device"
        "Corsair M75"
        "--mode"
        "direct"
        "--color"
        "000000"
      ];
      StateDirectory = "corsair-m75-lighting-off";
      Restart = "on-failure";
      RestartSec = 10;
      ProtectSystem = "strict";
      ProtectHome = true;
      NoNewPrivileges = true;
    };
  };
}
