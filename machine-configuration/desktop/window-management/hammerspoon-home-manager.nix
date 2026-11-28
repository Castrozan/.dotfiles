{ config, inputs, ... }:
{
  imports = [ inputs.hammerspoon.homeManagerModules.default ];

  programs.hammerspoon = {
    chromeProfileName = "Lucas";
    personalChromeLaunchCommand = "summon-chrome-personal-profile";
    workChromeLaunchCommand = "summon-chrome-work-profile";
    homeAssistantBinaryDirectory = "/etc/profiles/per-user/${config.home.username}/bin";
  };
}
