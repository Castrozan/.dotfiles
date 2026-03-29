{
  username,
  pkgs,
  lib,
  ...
}:
let
  homeAssistantConfigDirectory = "/home/${username}/.homeassistant";
  homeAssistantPipDepsDirectory = "/home/${username}/.homeassistant-pip-deps";

  installMideaLocalBeforeStart = pkgs.writeShellScript "install-midea-local-before-homeassistant" ''
    set -euo pipefail
    mkdir -p ${homeAssistantPipDepsDirectory}
    if [ ! -d "${homeAssistantPipDepsDirectory}/midealocal" ]; then
      ${pkgs.podman}/bin/podman run --rm \
        -v ${homeAssistantPipDepsDirectory}:/deps \
        ghcr.io/home-assistant/home-assistant:stable \
        pip install --target=/deps midea-local==6.5.0
    fi
  '';
in
{
  virtualisation.oci-containers.containers.homeassistant = {
    image = "ghcr.io/home-assistant/home-assistant:stable";
    volumes = [
      "${homeAssistantConfigDirectory}:/config"
      "${homeAssistantPipDepsDirectory}:/deps"
    ];
    environment = {
      PYTHONPATH = "/deps";
    };
    extraOptions = [ "--network=host" ];
  };

  systemd.services.podman-homeassistant = {
    serviceConfig.ExecStartPre = [
      installMideaLocalBeforeStart
    ];
  };
}
