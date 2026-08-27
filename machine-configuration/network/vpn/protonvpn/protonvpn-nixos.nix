{
  config,
  lib,
  pkgs,
  ...
}:
let
  protonParaguayService = "openvpn-proton-paraguay.service";
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
  services.openvpn.servers.proton-paraguay = {
    autoStart = false;
    config = "config ${config.age.secrets.proton-paraguay-openvpn-config.path}";
    authUserPass = config.age.secrets.proton-openvpn-credentials.path;
    updateResolvConf = true;
  };

  systemd.services.openvpn-proton-paraguay = {
    after = [ "agenix.service" ];
    wants = [ "agenix.service" ];
    serviceConfig.Restart = lib.mkForce "no";
  };

  environment.systemPackages = [
    vpnParaguay
    vpnOff
  ];

  environment.etc."openvpn/update-resolv-conf".source =
    "${pkgs.update-resolv-conf}/libexec/openvpn/update-resolv-conf";
}
