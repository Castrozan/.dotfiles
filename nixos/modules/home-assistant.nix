{
  username,
  pkgs,
  ...
}:
let
  installMideaLocalInContainer = pkgs.writeShellScript "install-midea-local-in-homeassistant" ''
    sleep 10
    ${pkgs.podman}/bin/podman exec homeassistant pip install --quiet midea-local==6.5.0
    ${pkgs.podman}/bin/podman exec homeassistant python -c "import midealocal" || exit 1
  '';
in
{
  virtualisation.oci-containers.containers.homeassistant = {
    image = "ghcr.io/home-assistant/home-assistant:stable";
    volumes = [
      "/home/${username}/.homeassistant:/config"
    ];
    extraOptions = [ "--network=host" ];
  };

  systemd.services.podman-homeassistant.serviceConfig.ExecStartPost = installMideaLocalInContainer;
}
