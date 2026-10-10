{
  username,
  pkgs,
  ...
}:
let
  homeAssistantImage = "ghcr.io/home-assistant/home-assistant:2026.3.4@sha256:916682086154a7390114a9788782b8efb199852d4f7d47066722c2bc5d1829e6";
  homeAssistantConfigDirectory = "/home/${username}/.homeassistant";
  homeAssistantPipDepsDirectory = "/home/${username}/.homeassistant-pip-deps";

  installMideaLocalBeforeStart = pkgs.writeShellScript "install-midea-local-before-homeassistant" ''
    set -euo pipefail
    mkdir -p ${homeAssistantPipDepsDirectory}
    if [ ! -d "${homeAssistantPipDepsDirectory}/midealocal" ]; then
      ${pkgs.docker}/bin/docker run --rm \
        -v ${homeAssistantPipDepsDirectory}:/deps \
        ${homeAssistantImage} \
        pip install --target=/deps midea-local==6.5.0
    fi
  '';
in
{
  virtualisation.oci-containers = {
    backend = "docker";
    containers.homeassistant = {
      image = homeAssistantImage;
      volumes = [
        "${homeAssistantConfigDirectory}:/config"
        "${homeAssistantPipDepsDirectory}:/deps"
      ];
      environment = {
        PYTHONPATH = "/deps";
      };
      extraOptions = [ "--network=host" ];
    };
  };

  systemd.services.docker-homeassistant = {
    serviceConfig.ExecStartPre = [
      installMideaLocalBeforeStart
    ];
  };
}
