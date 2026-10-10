{
  helpers,
  lib,
  self,
  ...
}:
let
  inherit (helpers) mkEvalCheck;
  homeAssistantConfiguration = self.nixosConfigurations.chise.config;
  homeAssistantContainer =
    homeAssistantConfiguration.virtualisation.oci-containers.containers.homeassistant;
  homeAssistantHomeDirectory = homeAssistantConfiguration.users.users.zanoni.home;
in
{
  chise-home-assistant-uses-the-shared-docker-engine =
    mkEvalCheck "chise-home-assistant-uses-the-shared-docker-engine"
      (
        homeAssistantConfiguration.virtualisation.oci-containers.backend == "docker"
        && homeAssistantConfiguration.virtualisation.docker.enable
        && !homeAssistantConfiguration.virtualisation.podman.enable
        && homeAssistantConfiguration.systemd.services ? docker-homeassistant
        && !(homeAssistantConfiguration.systemd.services ? podman-homeassistant)
      )
      "Home Assistant must share the existing Docker engine and stop declaring a separate Podman runtime";

  chise-home-assistant-preserves-its-state-and-lan-access =
    mkEvalCheck "chise-home-assistant-preserves-its-state-and-lan-access"
      (
        homeAssistantContainer.volumes == [
          "${homeAssistantHomeDirectory}/.homeassistant:/config"
          "${homeAssistantHomeDirectory}/.homeassistant-pip-deps:/deps"
        ]
        && homeAssistantContainer.environment.PYTHONPATH == "/deps"
        && builtins.elem "--network=host" homeAssistantContainer.extraOptions
        && lib.hasPrefix "ghcr.io/home-assistant/home-assistant:2026.3.4@sha256:" homeAssistantContainer.image
      )
      "Moving Home Assistant to Docker must preserve its existing application version, configuration, Midea dependencies and host networking";
}
