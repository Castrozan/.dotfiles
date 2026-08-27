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
    runtimeInputs = [
      pkgs.sudo
      pkgs.systemd
    ];
    text = ''
      exec sudo -n systemctl start ${protonParaguayService}
    '';
  };
  vpnOff = pkgs.writeShellApplication {
    name = "vpn-off";
    runtimeInputs = [
      pkgs.sudo
      pkgs.systemd
    ];
    text = ''
      exec sudo -n systemctl stop ${protonParaguayService}
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
}
