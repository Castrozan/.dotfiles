{ inputs, username, ... }:
{
  imports = [ inputs.home-assistant.nixosModules.default ];

  homeAssistant = {
    configDirectory = "/home/${username}/.homeassistant";
    pipDependenciesDirectory = "/home/${username}/.homeassistant-pip-deps";
  };
}
