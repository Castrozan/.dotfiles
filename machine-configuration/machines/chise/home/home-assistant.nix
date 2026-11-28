{ inputs, ... }:
{
  imports = [ inputs.home-assistant.homeManagerModules.default ];

  homeAssistant = {
    airConditionerEntityId = "climate.150633094104375_climate";
    lightEntityIds = [
      "light.bedroom"
      "light.kitchen"
      "light.livingroom"
      "light.bathroom"
    ];
    tokenFile = "~/.secrets/home-assistant-token";
    mideaConfigEntriesFile = "~/.homeassistant/.storage/core.config_entries";
  };
}
