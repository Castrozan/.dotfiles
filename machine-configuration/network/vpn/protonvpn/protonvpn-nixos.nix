{
  config,
  lib,
  pkgs,
  ...
}:
let
  protonParaguayService = "openvpn-proton-paraguay.service";
  updateSystemdResolved = "${pkgs.update-systemd-resolved}/libexec/openvpn/update-systemd-resolved";
  vpnParaguay = pkgs.writeShellApplication {
    name = "vpn-py";
    runtimeInputs = [ pkgs.systemd ];
    text = ''
      exec /run/wrappers/bin/sudo -n systemctl start ${protonParaguayService}
    '';
  };
  vpnOff = pkgs.writeShellApplication {
    name = "vpn-off";
    runtimeInputs = [ pkgs.systemd ];
    text = ''
      exec /run/wrappers/bin/sudo -n systemctl stop ${protonParaguayService}
    '';
  };
in
{
  services.resolved.enable = true;

  services.openvpn.servers.proton-paraguay = {
    autoStart = false;
    config = ''
      config ${config.age.secrets.proton-paraguay-openvpn-config.path}
      ifconfig-ipv6 fd15:53b6:dead::2/64 fd15:53b6:dead::1
      redirect-gateway ipv6
      block-ipv6
      dhcp-option DOMAIN-ROUTE .
      up-restart
      down-pre
    '';
    authUserPass = config.age.secrets.proton-openvpn-credentials.path;
    up = updateSystemdResolved;
    down = updateSystemdResolved;
    updateResolvConf = false;
  };

  systemd.services.openvpn-proton-paraguay = {
    after = [
      "agenix.service"
      "systemd-resolved.service"
    ];
    wants = [ "agenix.service" ];
    requires = [ "systemd-resolved.service" ];
    serviceConfig.Restart = lib.mkForce "no";
  };

  environment.systemPackages = [
    vpnParaguay
    vpnOff
  ];
}
