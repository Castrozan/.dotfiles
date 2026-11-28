{ config, inputs, ... }:
{
  imports = [ inputs.read-it-later.homeManagerModules.watcher ];

  clawdeAgentSkillSets.ril-watcher = [
    "ril"
    "forge"
    "browser"
    "desktop"
    "research"
  ];

  programs.ril.watcher.skillDirectories = [
    config.clawdeAgentSkillSetDirectories.ril-watcher
    "${config.home.homeDirectory}/.dotfiles"
    "${config.home.homeDirectory}/vault"
  ];
}
